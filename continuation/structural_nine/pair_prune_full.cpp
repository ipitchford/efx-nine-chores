// Exact two-inequality outer-cone pruning of ordinally robust pairs.
#include <algorithm>
#include <array>
#include <chrono>
#include <cstdint>
#include <fstream>
#include <iostream>
#include <stdexcept>
#include <string>
#include <vector>

struct Atom {
  std::array<int,9> u{};
  std::uint16_t positive=0,negative=0;
};
struct Allocation {
  bool robust=false;
  std::array<std::vector<std::uint16_t>,2> rows;
  unsigned internal=0; // 0: no two-atom contradiction; 2: weak impossible; 3: equality required
};

bool read_id(std::ifstream &f,std::uint32_t &id) {
  id=0;
  for(unsigned k=0;k<4;k++) {
    int c=f.get();if(c==EOF)return false;id|=static_cast<std::uint32_t>(c)<<(8*k);
  }
  return true;
}
void write_pair(std::ofstream &f,std::uint32_t a,std::uint32_t b) {
  for(auto id:{a,b})for(unsigned byte=0;byte<4;byte++) f.put(static_cast<char>((id>>(8*byte))&255));
}

int main(int argc,char** argv) {
  if(argc!=6)throw std::runtime_error("prune_input accepted_pairs weak_survivors generic_survivors summary");
  const auto started=std::chrono::steady_clock::now();
  auto elapsed=[&](){return std::chrono::duration<double>(std::chrono::steady_clock::now()-started).count();};
  std::ifstream input(argv[1]);std::size_t n=0,m=0,robust=0;input>>n>>m>>robust;
  if(!input || m>=65536)throw std::runtime_error("Bad input header");
  std::vector<Atom> atoms(m);
  for(auto &a:atoms)for(int k=0;k<9;k++) {
    input>>a.u[k];
    if(a.u[k]>0)a.positive|=1u<<k;
    if(a.u[k]<0)a.negative|=1u<<k;
  }
  std::vector<Allocation> allocations(19683);
  std::vector<std::uint32_t> ids;
  for(std::size_t k=0;k<n;k++) {
    std::uint32_t aid;unsigned is_robust,n1,n2;input>>aid>>is_robust>>n1>>n2;
    if(aid>=allocations.size())throw std::runtime_error("Bad allocation ID");
    auto &a=allocations[aid];a.robust=is_robust;
    a.rows[0].resize(n1);a.rows[1].resize(n2);
    for(auto &row:a.rows)for(auto &v:row) {
      unsigned v0;input>>v0;if(v0>=m)throw std::runtime_error("Bad atom ID");v=v0;
    }
    ids.push_back(aid);
  }
  if(!input)throw std::runtime_error("Incomplete input");
  std::vector<std::uint8_t> cache((m*(m+1)/2+3)/4,0);
  std::uint64_t lookups=0,ratio_tests=0,sign_rejections=0,cache_hits=0;
  auto obstruction=[&](std::uint16_t first,std::uint16_t second) {
    ++lookups;const auto &a=atoms[first];const auto &b=atoms[second];
    if(!a.negative || !b.negative)return 2u;
    if((a.negative & ~b.positive)||(b.negative & ~a.positive)) {
      ++sign_rejections;return 1u;
    }
    const std::size_t hi=std::max(first,second),lo=std::min(first,second),key=hi*(hi+1)/2+lo;
    const unsigned shift=2*(key%4),stored=(cache[key/4]>>shift)&3;
    if(stored){++cache_hits;return stored;}
    ++ratio_tests;
    int ln=0,ld=1,un=1,ud=0;unsigned result=1;
    bool possible=true;
    for(int k=0;k<9;k++) {
      const int u=-a.u[k],v=-b.u[k];
      if(u>0&&(ud==0||(-v)*ud<un*u)){un=-v;ud=u;}
      if(v>0&&v*ld>ln*(-u)){ln=v;ld=-u;}
      if(ud&&ln*ud>un*ld){possible=false;break;}
    }
    if(possible) {
      if(ln*ud<un*ld)result=2;
      else {
        result=3;
        for(int k=0;k<9;k++)if(ln*a.u[k]+ld*b.u[k]>0){result=2;break;}
      }
    }
    cache[key/4]|=static_cast<std::uint8_t>(result<<shift);return result;
  };
  std::uint64_t internal_weak=0,internal_wall=0;
  for(auto aid:ids) {
    auto &a=allocations[aid];
    for(const auto &row:a.rows) {
      for(auto u:row)if(!atoms[u].negative)a.internal=2;
      for(std::size_t i=0;i<row.size()&&a.internal!=2;i++)for(std::size_t j=i+1;j<row.size();j++) {
        const auto result=obstruction(row[i],row[j]);
        if(result==2){a.internal=2;break;}
        if(result==3)a.internal=3;
      }
    }
    internal_weak+=a.internal==2;internal_wall+=a.internal==3;
  }
  std::ifstream pairs(argv[2],std::ios::binary);
  std::ofstream weak(argv[3],std::ios::binary),generic(argv[4],std::ios::binary);
  std::uint64_t tested=0,weak_removed=0,wall_removed=0,survived=0;
  std::uint64_t by_weak_internal=0,by_weak_cross=0;
  std::uint32_t aid,bid;
  while(read_id(pairs,aid)) {
    if(!read_id(pairs,bid)||aid>=19683||bid>=19683)throw std::runtime_error("Malformed pair stream");
    ++tested;
    const auto &a=allocations[aid];const auto &b=allocations[bid];
    if(a.internal==2||b.internal==2){++weak_removed;++by_weak_internal;continue;}
    bool has_wall=a.internal==3||b.internal==3,impossible=false;
    for(int row=0;row<2&&!impossible;row++) {
      for(auto u:a.rows[row]) {
        for(auto v:b.rows[row]) {
          const auto result=obstruction(u,v);
          if(result==2){impossible=true;break;}
          if(result==3)has_wall=true;
        }
        if(impossible)break;
      }
    }
    if(impossible){++weak_removed;++by_weak_cross;continue;}
    write_pair(weak,aid,bid);
    if(has_wall){++wall_removed;continue;}
    ++survived;write_pair(generic,aid,bid);
  }
  std::ofstream summary(argv[5]);
  summary<<"{\n\"status\":\"complete\",\n\"pairs_tested\":"<<tested<<",\n"
    <<"\"weak_infeasibility_removed\":"<<weak_removed<<",\n"
    <<"\"weak_infeasibility_internal\":"<<by_weak_internal<<",\n"
    <<"\"weak_infeasibility_cross\":"<<by_weak_cross<<",\n"
    <<"\"requires_subset_equality_removed\":"<<wall_removed<<",\n"
    <<"\"generic_survivors\":"<<survived<<",\n"
    <<"\"allocations_with_internal_weak_obstruction\":"<<internal_weak<<",\n"
    <<"\"allocations_with_internal_equality_obstruction\":"<<internal_wall<<",\n"
    <<"\"unique_outer_atoms\":"<<m<<",\n\"atom_pair_lookups\":"<<lookups<<",\n"
    <<"\"sign_rejections\":"<<sign_rejections<<",\n\"ratio_tests\":"<<ratio_tests<<",\n"
    <<"\"cache_hits\":"<<cache_hits<<",\n\"cache_bytes\":"<<cache.size()<<",\n"
    <<"\"seconds\":"<<elapsed()<<"\n}\n";
  std::cout<<"tested="<<tested<<" weak_removed="<<weak_removed<<" wall_removed="<<wall_removed
           <<" generic_survivors="<<survived<<" seconds="<<elapsed()<<"\n";
}
