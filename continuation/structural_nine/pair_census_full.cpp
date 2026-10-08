// Exact robust-pair census. No floating point enters a feasibility decision.
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
  std::uint16_t positive=0, negative=0;
};
struct Allocation {
  std::uint32_t id=0;
  unsigned flags=0;
  std::vector<std::uint16_t> atoms;
};

int main(int argc, char** argv) {
  if(argc!=5) throw std::runtime_error("input.txt pairs.bin summary.json seconds");
  const auto started=std::chrono::steady_clock::now();
  auto elapsed=[&](){return std::chrono::duration<double>(std::chrono::steady_clock::now()-started).count();};
  const int seconds=std::stoi(argv[4]);
  std::ifstream input(argv[1]);
  std::size_t n=0,m=0,robust=0,surjective=0;
  input>>n>>m>>robust>>surjective;
  if(!input || m>=65536) throw std::runtime_error("Invalid input header");
  std::vector<Atom> atoms(m);
  for(auto &a:atoms) for(int k=0;k<9;k++) {
    input>>a.u[k];
    if(a.u[k]>0) a.positive |= 1u<<k;
    if(a.u[k]<0) a.negative |= 1u<<k;
    if(std::abs(a.u[k])>9) throw std::runtime_error("Unexpected coefficient bound");
  }
  std::vector<Allocation> allocations(n);
  for(auto &a:allocations) {
    unsigned count=0; input>>a.id>>a.flags>>count;
    if(count==0 || count>4) throw std::runtime_error("Invalid clause size");
    a.atoms.resize(count);
    for(auto &atom:a.atoms) {
      unsigned id=0; input>>id;
      if(id>=m) throw std::runtime_error("Invalid atom index");
      atom=static_cast<std::uint16_t>(id);
    }
  }
  if(!input) throw std::runtime_error("Incomplete input");
  const std::size_t cache_entries=m*(m+1)/2;
  std::vector<std::uint8_t> cache((cache_entries+3)/4,0);
  std::uint64_t lookups=0, sign_rejections=0, ratio_tests=0, cache_hits=0;
  auto incompatible=[&](std::uint16_t first,std::uint16_t second) {
    ++lookups;
    const auto &a=atoms[first]; const auto &b=atoms[second];
    // Both atoms are individually feasible, so both multipliers must be
    // strictly positive. Every positive coefficient needs a negative mate.
    if((a.positive & ~b.negative) || (b.positive & ~a.negative)) {
      ++sign_rejections; return false;
    }
    const std::size_t hi=std::max(first,second),lo=std::min(first,second);
    const std::size_t key=hi*(hi+1)/2+lo;
    const unsigned shift=2*(key%4);
    const unsigned stored=(cache[key/4]>>shift)&3;
    if(stored) { ++cache_hits; return stored==2; }
    ++ratio_tests;
    int lower_num=0,lower_den=1,upper_num=1,upper_den=0;
    bool result=true;
    for(int k=0;k<9;k++) {
      const int u=a.u[k],v=b.u[k];
      if(u>0 && (upper_den==0 || (-v)*upper_den<upper_num*u)) {
        upper_num=-v;upper_den=u;
      }
      if(v>0 && v*lower_den>lower_num*(-u)) {
        lower_num=v;lower_den=-u;
      }
      if(upper_den && lower_num*upper_den>upper_num*lower_den) {
        result=false;break;
      }
    }
    cache[key/4] |= static_cast<std::uint8_t>((result?2:1)<<shift);
    return result;
  };
  std::ofstream output(argv[2],std::ios::binary);
  std::uint64_t tested=0,accepted=0;
  std::array<std::uint64_t,3> by_all_minima{},by_first_minimum{};
  bool complete=true;
  for(std::size_t i=0;i<n && complete;i++) {
    for(std::size_t j=i+1;j<n;j++) {
      if(tested%16384==0 && elapsed()>=seconds) {complete=false;break;}
      ++tested;
      bool covers=true;
      for(auto a:allocations[i].atoms) {
        for(auto b:allocations[j].atoms) {
          if(!incompatible(a,b)) {covers=false;break;}
        }
        if(!covers) break;
      }
      if(covers) {
        ++accepted;
        ++by_all_minima[(allocations[i].flags==7)+(allocations[j].flags==7)];
        ++by_first_minimum[(bool)(allocations[i].flags&1)+(bool)(allocations[j].flags&1)];
        for(auto id:{allocations[i].id,allocations[j].id})
          for(unsigned byte=0;byte<4;byte++) output.put(static_cast<char>((id>>(8*byte))&255));
      }
      if(tested%10000000==0)
        std::cerr<<"{\"tested\":"<<tested<<",\"accepted\":"<<accepted<<",\"seconds\":"<<elapsed()<<"}\n";
    }
  }
  output.close();
  if(complete && by_all_minima[2]!=1048) throw std::runtime_error("Known all-minima subfamily mismatch");
  std::ofstream summary(argv[3]);
  summary<<"{\n\"status\":\""<<(complete?"complete":"time_limit")<<"\",\n"
    <<"\"surjective_allocations\":"<<surjective<<",\n\"robust_singles_removed\":"<<robust<<",\n"
    <<"\"nonrobust_allocations\":"<<n<<",\n\"unique_feasible_atoms\":"<<m<<",\n"
    <<"\"allocation_pairs_tested\":"<<tested<<",\n\"total_possible_pairs\":"<<n*(n-1)/2<<",\n"
    <<"\"accepted_pairs\":"<<accepted<<",\n"
    <<"\"accepted_by_number_all_minima_owned\":["<<by_all_minima[0]<<","<<by_all_minima[1]<<","<<by_all_minima[2]<<"],\n"
    <<"\"accepted_by_number_first_minimum_owned\":["<<by_first_minimum[0]<<","<<by_first_minimum[1]<<","<<by_first_minimum[2]<<"],\n"
    <<"\"atom_pair_lookups\":"<<lookups<<",\n\"sign_rejections\":"<<sign_rejections<<",\n"
    <<"\"exact_ratio_tests\":"<<ratio_tests<<",\n\"cache_hits\":"<<cache_hits<<",\n"
    <<"\"cache_bytes\":"<<cache.size()<<",\n\"seconds\":"<<elapsed()<<",\n"
    <<"\"pairs_format\":\"Repeated two uint32 little-endian allocation IDs\"\n}\n";
  std::cout<<"completed="<<complete<<" tested="<<tested<<" accepted="<<accepted<<" seconds="<<elapsed()<<"\n";
}
