// Producer-only performance observation; no SMT/SAT search or proof claim.
#define main unused_cached_producer_main
#include "rup_dependency_producer_v3.cpp"
#undef main
#include <sys/resource.h>
int main(int argc,char**argv){
    try{
        if(argc!=3)throw runtime_error("usage: profile_source_unit_closure CAPTURE REPORT_JSON");
        filesystem::path capture=argv[1],report=argv[2];
        if(filesystem::exists(report))throw runtime_error("use a fresh report path");
        Engine e;long inputs=0,theories=0;
        auto start=chrono::steady_clock::now();
        auto load=[&](string const& name,int kind,long& count){
            ifstream f(capture/name);if(!f)throw runtime_error("missing source");string line;
            while(getline(f,line))e.add(parse_clause(line),kind,count++);
        };
        load("input_clauses.jsonl",1,inputs);load("theory_clauses.jsonl",2,theories);
        Id source_count=e.db.size()-1;size_t direct_units=e.units.size();
        auto loaded=chrono::steady_clock::now();e.initialize_base();auto closed=chrono::steady_clock::now();
        rusage usage{};getrusage(RUSAGE_SELF,&usage);
        ofstream out(report);
        out<<"{\"status\":\"SOURCE_ONLY_UNIT_CLOSURE_PROFILE_NOT_A_PROOF\",\"input_records\":"<<inputs
           <<",\"theory_records\":"<<theories<<",\"direct_source_unit_clauses\":"<<direct_units
           <<",\"forced_boolean_variables\":"<<e.base_trail_size<<",\"derived_unit_nodes\":"<<(e.db.size()-1-source_count)
           <<",\"source_only_unit_conflict\":"<<(e.base_conflict?"true":"false")
           <<",\"source_load_seconds\":"<<chrono::duration<double>(loaded-start).count()
           <<",\"source_closure_seconds_including_unit_hint_construction\":"<<chrono::duration<double>(closed-loaded).count()
           <<",\"peak_rss_kib\":"<<usage.ru_maxrss<<"}\n";
        out.close();sync_file(report);cout<<"profile complete\n";return 0;
    }catch(exception const& error){cerr<<error.what()<<'\n';return 2;}
}
