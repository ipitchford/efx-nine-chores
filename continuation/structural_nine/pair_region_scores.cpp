// Number of maximal outer-cone premises for each archived robust pair.
#include <array>
#include <cstdint>
#include <fstream>
#include <iostream>
#include <stdexcept>
#include <vector>

struct Allocation {std::array<std::vector<std::uint16_t>,2> rows;};
bool read_id(std::ifstream &f,std::uint32_t &id) {
  id=0;for(unsigned k=0;k<4;k++){int c=f.get();if(c==EOF)return false;id|=static_cast<std::uint32_t>(c)<<(8*k);}return true;
}
int main(int argc,char**argv) {
  if(argc!=5)throw std::runtime_error("prune_input pairs scores summary");
  std::ifstream input(argv[1]);std::size_t n,m,robust;input>>n>>m>>robust;
  std::vector<std::array<int,9>> atoms(m);for(auto &a:atoms)for(auto &v:a)input>>v;
  std::vector<Allocation> allocations(19683);
  for(std::size_t k=0;k<n;k++) {
    unsigned aid,r,n1,n2;input>>aid>>r>>n1>>n2;
    auto &a=allocations.at(aid);a.rows[0].resize(n1);a.rows[1].resize(n2);
    for(auto &row:a.rows)for(auto &v:row){unsigned v0;input>>v0;v=v0;}
  }
  if(!input)throw std::runtime_error("Incomplete input");
  const std::size_t words=(m+63)/64;
  std::vector<std::uint64_t> implication(m*words,0);
  for(std::size_t p=0;p<m;p++)for(std::size_t t=0;t<m;t++) {
    bool dominates=true;for(int k=0;k<9;k++)if(atoms[t][k]>atoms[p][k]){dominates=false;break;}
    if(dominates)implication[p*words+t/64]|=1ULL<<(t%64);
  }
  auto dom=[&](unsigned p,unsigned t){return bool(implication[p*words+t/64]&(1ULL<<(t%64)));};
  std::ifstream pairs(argv[2],std::ios::binary);std::ofstream scores(argv[3],std::ios::binary);
  std::array<std::uint64_t,256> counts{};std::uint64_t total=0;std::uint32_t aid,bid;
  while(read_id(pairs,aid)) {
    if(!read_id(pairs,bid))throw std::runtime_error("Incomplete pair");
    unsigned score=0;const auto &a=allocations.at(aid);const auto &b=allocations.at(bid);
    for(int row=0;row<2;row++) {
      for(auto u:a.rows[row]) {
        bool redundant=false;for(auto v:b.rows[row])if(u!=v&&dom(v,u)){redundant=true;break;}
        score+=!redundant;
      }
      for(auto v:b.rows[row]) {
        bool redundant=false;for(auto u:a.rows[row])if(dom(u,v)){redundant=true;break;}
        score+=!redundant;
      }
    }
    if(score>=256)throw std::runtime_error("Score overflow");
    scores.put(static_cast<char>(score));++counts[score];++total;
  }
  std::ofstream summary(argv[4]);summary<<"{\"pairs\":"<<total<<",\"score_counts\":{";bool first=true;
  for(unsigned k=0;k<256;k++)if(counts[k]) {
    if(!first)summary<<",";first=false;summary<<"\""<<k<<"\":"<<counts[k];
  }
  summary<<"}}\n";std::cout<<"scored="<<total<<"\n";
}
