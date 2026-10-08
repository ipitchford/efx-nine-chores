// Remove a pair region whenever exact cone dominance places it inside one
// of the 3238 already retained singleton regions. No solver is used.
#include <algorithm>
#include <array>
#include <chrono>
#include <cstdint>
#include <fstream>
#include <iostream>
#include <stdexcept>
#include <vector>

struct Allocation {
  std::uint32_t id=0;bool robust=false;
  std::array<std::vector<std::uint16_t>,2> rows;
};
bool read_id(std::ifstream &f,std::uint32_t &id) {
  id=0;for(unsigned k=0;k<4;k++){int c=f.get();if(c==EOF)return false;id|=static_cast<std::uint32_t>(c)<<(8*k);}return true;
}
void write_id(std::ofstream &f,std::uint32_t id) {
  for(unsigned byte=0;byte<4;byte++)f.put(static_cast<char>((id>>(8*byte))&255));
}
int main(int argc,char** argv) {
  if(argc!=6)throw std::runtime_error("prune_input generic_pairs survivors dominance_records summary");
  const auto started=std::chrono::steady_clock::now();
  auto elapsed=[&](){return std::chrono::duration<double>(std::chrono::steady_clock::now()-started).count();};
  std::ifstream input(argv[1]);std::size_t n,m,nrobust;input>>n>>m>>nrobust;
  std::vector<std::array<int,9>> atoms(m);for(auto &a:atoms)for(auto &v:a)input>>v;
  std::vector<Allocation> allocations(n);std::vector<int> positions(19683,-1);
  for(std::size_t k=0;k<n;k++) {
    auto &a=allocations[k];unsigned robust,n1,n2;input>>a.id>>robust>>n1>>n2;a.robust=robust;
    a.rows[0].resize(n1);a.rows[1].resize(n2);
    for(auto &row:a.rows)for(auto &v:row){unsigned v0;input>>v0;if(v0>=m)throw std::runtime_error("Bad atom");v=v0;}
    positions[a.id]=k;
  }
  if(!input)throw std::runtime_error("Incomplete input");
  std::vector<unsigned> robust;
  for(unsigned i=0;i<n;i++)if(allocations[i].robust)robust.push_back(i);
  std::sort(robust.begin(),robust.end(),[&](unsigned a,unsigned b) {
    const auto size_a=allocations[a].rows[0].size()+allocations[a].rows[1].size();
    const auto size_b=allocations[b].rows[0].size()+allocations[b].rows[1].size();
    return size_a!=size_b?size_a<size_b:allocations[a].id<allocations[b].id;
  });
  if(robust.size()!=nrobust)throw std::runtime_error("Robust count mismatch");
  for(auto s:robust)if(allocations[s].rows[0].size()+allocations[s].rows[1].size()>16)
    throw std::runtime_error("Singleton mask too large");
  const std::size_t words=(m+63)/64;
  std::vector<std::uint64_t> implication(m*words,0);
  std::uint64_t dominance_relations=0;
  for(std::size_t premise=0;premise<m;premise++)for(std::size_t target=0;target<m;target++) {
    bool dominates=true;
    for(int k=0;k<9;k++)if(atoms[target][k]>atoms[premise][k]){dominates=false;break;}
    if(dominates){implication[premise*words+target/64]|=1ULL<<(target%64);++dominance_relations;}
  }
  std::cerr<<"implications_complete seconds="<<elapsed()<<"\n";
  std::vector<std::uint16_t> missing(n*nrobust,0);
  std::vector<int> single_cover(n,-1);
  std::array<std::vector<std::uint64_t>,2> implied;
  for(auto &row:implied)row.resize(words);
  for(std::size_t a=0;a<n;a++) {
    for(int row=0;row<2;row++) {
      std::fill(implied[row].begin(),implied[row].end(),0);
      for(auto v:allocations[a].rows[row])for(std::size_t w=0;w<words;w++)
        implied[row][w]|=implication[v*words+w];
    }
    for(std::size_t k=0;k<nrobust;k++) {
      std::uint16_t mask=0;unsigned bit=0;
      for(int row=0;row<2;row++)for(auto target:allocations[robust[k]].rows[row]) {
        if(!(implied[row][target/64]&(1ULL<<(target%64))))mask|=1u<<bit;
        ++bit;
      }
      missing[a*nrobust+k]=mask;
      if(mask==0 && single_cover[a]<0)single_cover[a]=k;
    }
  }
  std::cerr<<"missing_masks_complete seconds="<<elapsed()<<"\n";
  std::ifstream pairs(argv[2],std::ios::binary);
  std::ofstream survivors(argv[3],std::ios::binary),certificates(argv[4],std::ios::binary);
  std::uint64_t tested=0,dominated=0,remaining=0,from_single=0;
  std::vector<std::uint64_t> cover_counts(nrobust,0);
  std::uint32_t aid,bid;
  while(read_id(pairs,aid)) {
    if(!read_id(pairs,bid)||aid>=19683||bid>=19683||positions[aid]<0||positions[bid]<0)
      throw std::runtime_error("Invalid pair stream");
    ++tested;const auto a=positions[aid],b=positions[bid];int cover=-1;
    if(single_cover[a]>=0){cover=single_cover[a];++from_single;}
    else if(single_cover[b]>=0){cover=single_cover[b];++from_single;}
    else {
      const auto *ma=missing.data()+a*nrobust,*mb=missing.data()+b*nrobust;
      for(std::size_t k=0;k<nrobust;k++)if((ma[k]&mb[k])==0){cover=k;break;}
    }
    if(cover>=0) {
      ++dominated;++cover_counts[cover];write_id(certificates,aid);write_id(certificates,bid);
      write_id(certificates,allocations[robust[cover]].id);
    } else {++remaining;write_id(survivors,aid);write_id(survivors,bid);}
  }
  std::ofstream summary(argv[5]);
  summary<<"{\n\"status\":\"complete\",\n\"pairs_tested\":"<<tested<<",\n"
    <<"\"dominated_by_robust_single\":"<<dominated<<",\n\"dominated_by_one_member_region\":"<<from_single<<",\n"
    <<"\"surviving_pairs\":"<<remaining<<",\n\"atom_dominance_relations\":"<<dominance_relations<<",\n"
    <<"\"missing_mask_bytes\":"<<missing.size()*sizeof(std::uint16_t)<<",\n"
    <<"\"implication_bytes\":"<<implication.size()*sizeof(std::uint64_t)<<",\n"
    <<"\"seconds\":"<<elapsed()<<"\n}\n";
  std::cout<<"tested="<<tested<<" dominated="<<dominated<<" survivors="<<remaining<<" seconds="<<elapsed()<<"\n";
}
