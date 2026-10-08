// Untrusted watched-propagation dependency producer. Independent checking required.
#include <algorithm>
#include <chrono>
#include <cstdlib>
#include <filesystem>
#include <fstream>
#include <iostream>
#include <stdexcept>
#include <string>
#include <unordered_map>
#include <vector>
#include <fcntl.h>
#include <unistd.h>
using namespace std;
using Id = int;
struct VecHash {
    size_t operator()(vector<int> const& v) const noexcept {
        size_t h=1469598103934665603ULL;
        for(int x:v) { h^=static_cast<unsigned>(x);h*=1099511628211ULL; }
        return h;
    }
};
struct Clause {
    vector<int> lits;
    vector<Id> hints;
    int w0=0,w1=1;
    int kind=0; // 0=null input, 1=input, 2=theory, 3=RUP
    long source=-1;
};
struct Parsed { bool is_null=false; vector<int> lits; };
Parsed parse_clause(string const& line) {
    auto p=line.find("\"clause\"");
    if(p==string::npos)throw runtime_error("missing clause field");
    p=line.find(':',p);if(p==string::npos)throw runtime_error("missing colon");
    ++p;while(p<line.size() && isspace(static_cast<unsigned char>(line[p])))++p;
    if(line.compare(p,4,"null")==0)return {true,{}};
    if(p==line.size() || line[p++]!='[')throw runtime_error("expected clause array");
    Parsed out;
    while(true) {
        while(p<line.size() && isspace(static_cast<unsigned char>(line[p])))++p;
        if(p<line.size() && line[p]==']')break;
        char* end=nullptr;long value=strtol(line.c_str()+p,&end,10);
        if(end==line.c_str()+p || !value || value>2000000000L || value< -2000000000L)
            throw runtime_error("bad literal");
        out.lits.push_back(static_cast<int>(value));p=end-line.c_str();
        while(p<line.size() && isspace(static_cast<unsigned char>(line[p])))++p;
        if(p<line.size() && line[p]==',')++p;
        else if(p<line.size() && line[p]==']')break;
        else throw runtime_error("malformed clause array");
    }
    if(!is_sorted(out.lits.begin(),out.lits.end()) || adjacent_find(out.lits.begin(),out.lits.end())!=out.lits.end())
        throw runtime_error("capture clause is not canonical");
    for(int x:out.lits)if(binary_search(out.lits.begin(),out.lits.end(),-x))throw runtime_error("tautological capture clause");
    return out;
}
void ints(ostream& out,vector<int> const& values) {
    out<<'[';bool comma=false;for(int x:values){if(comma)out<<',';out<<x;comma=true;}out<<']';
}
void sync_file(filesystem::path const& path) {
    int fd=open(path.c_str(),O_RDONLY);
    if(fd<0)throw runtime_error("cannot open output for fsync");
    int result=fsync(fd);close(fd);
    if(result)throw runtime_error("output fsync failed");
}
struct Engine {
    vector<Clause> db{Clause()};
    vector<vector<Id>> watches;
    vector<Id> units;
    unordered_map<vector<int>,Id,VecHash> identical;
    vector<signed char> values;
    vector<Id> reasons;
    vector<int> trail;
    vector<Id> ordered;
    vector<unsigned> needed;
    unsigned stamp=0;
    Id empty_axiom=0;
    long propagations=0,checks=0;
    void ensure(int v) {
        if(static_cast<int>(values.size())<=v){values.resize(v+1,0);reasons.resize(v+1,0);watches.resize(2*(v+1)+2);}
    }
    static size_t wi(int literal){return 2*static_cast<size_t>(abs(literal))+(literal<0);}
    int val(int lit) const {return lit>0?values[lit]:-values[-lit];}
    void assign(int lit,Id reason) {int v=abs(lit);values[v]=lit>0?1:-1;reasons[v]=reason;trail.push_back(lit);}
    Id add(Parsed const& p,int kind,long source,vector<Id> hints={}) {
        Id id=db.size();Clause c;c.lits=p.lits;c.kind=p.is_null?0:kind;c.source=source;c.hints=move(hints);
        db.push_back(move(c));needed.resize(db.size(),0);
        if(p.is_null)return id;
        for(int x:p.lits)ensure(abs(x));
        auto [it,fresh]=identical.emplace(p.lits,id);
        if(!fresh)return id; // exact duplicate; older clause suffices for propagation
        if(p.lits.empty()){if(!empty_axiom)empty_axiom=id;}
        else if(p.lits.size()==1)units.push_back(id);
        else {watches[wi(p.lits[0])].push_back(id);watches[wi(p.lits[1])].push_back(id);}
        return id;
    }
    vector<Id> conflict_slice(Id conflict) {
        ++stamp;if(!stamp){fill(needed.begin(),needed.end(),0);++stamp;}
        vector<int> todo;needed[conflict]=stamp;
        for(int lit:db[conflict].lits){if(val(lit)!=-1)throw runtime_error("conflict clause not false");todo.push_back(abs(lit));}
        while(!todo.empty()) {
            int v=todo.back();todo.pop_back();Id id=reasons[v];
            if(!id || needed[id]==stamp)continue;
            needed[id]=stamp;
            for(int lit:db[id].lits)if(abs(lit)!=v){
                if(val(lit)!=-1)throw runtime_error("reason dependency not false");
                todo.push_back(abs(lit));
            }
        }
        vector<Id> result;for(Id id:ordered)if(needed[id]==stamp)result.push_back(id);
        if(result.empty() || result.back()!=conflict)throw runtime_error("missing final conflict reason");
        return result;
    }
    bool check(vector<int> const& candidate,vector<Id>& hint) {
        ++checks;ordered.clear();trail.clear();
        for(int lit:candidate)ensure(abs(lit));
        auto reset=[&](){for(int lit:trail){values[abs(lit)]=0;reasons[abs(lit)]=0;}trail.clear();};
        auto finish=[&](Id conflict){ordered.push_back(conflict);hint=conflict_slice(conflict);reset();return true;};
        for(int lit:candidate){if(val(-lit)==-1)throw runtime_error("tautological RUP candidate");if(val(-lit)==0)assign(-lit,0);}
        if(empty_axiom)return finish(empty_axiom);
        for(Id id:units){int lit=db[id].lits[0];if(val(lit)==-1)return finish(id);if(!val(lit)){ordered.push_back(id);assign(lit,id);}}
        size_t head=0;
        while(head<trail.size()) {
            int false_lit=-trail[head++];++propagations;
            auto& list=watches[wi(false_lit)];size_t k=0;
            while(k<list.size()) {
                Id id=list[k];Clause& c=db[id];
                bool first=c.lits[c.w0]==false_lit;
                if(!first && c.lits[c.w1]!=false_lit)throw runtime_error("stale watched literal");
                int other_pos=first?c.w1:c.w0;int other=c.lits[other_pos];
                if(val(other)==1){++k;continue;}
                int replacement=-1;
                for(int pos=0;pos<static_cast<int>(c.lits.size());++pos)
                    if(pos!=other_pos && val(c.lits[pos])!=-1){replacement=pos;break;}
                if(replacement>=0){
                    if(first)c.w0=replacement;else c.w1=replacement;
                    watches[wi(c.lits[replacement])].push_back(id);list[k]=list.back();list.pop_back();continue;
                }
                if(val(other)==-1)return finish(id);
                ordered.push_back(id);assign(other,id);++k;
            }
        }
        reset();hint.clear();return false;
    }
};
int main(int argc,char**argv) {
    try {
        if(argc!=3)throw runtime_error("usage: rup_dependency_producer CAPTURE OUT_DIRECTORY");
        filesystem::path capture=argv[1],out=argv[2];
        if(filesystem::exists(out))throw runtime_error("use a fresh output directory");
        filesystem::create_directories(out);
        auto start=chrono::steady_clock::now();Engine e;long input_count=0,theory_count=0,rup_processed=0;
        auto load=[&](string const& name,int kind,long& count){
            ifstream f(capture/name);if(!f)throw runtime_error("cannot read "+name);string line;
            while(getline(f,line)){Parsed p=parse_clause(line);if(kind==2 && p.is_null)throw runtime_error("null theory");e.add(p,kind,count++);}
        };
        load("input_clauses.jsonl",1,input_count);load("theory_clauses.jsonl",2,theory_count);
        Id base=e.db.size()-1,final_id=0;vector<Id> hints;
        // An immediate unit contradiction is already a complete shorter refutation.
        if(e.check({},hints))final_id=e.add({false,{}},3,-1,move(hints));
        ifstream stream(capture/"rup_clauses.jsonl");if(!stream)throw runtime_error("missing RUP stream");string line;
        while(!final_id && getline(stream,line)) {
            Parsed p=parse_clause(line);if(p.is_null)throw runtime_error("null RUP record");
            auto same=e.identical.find(p.lits);
            if(same!=e.identical.end())hints={same->second};
            else if(!e.check(p.lits,hints))throw runtime_error("RUP failed at source index "+to_string(rup_processed));
            Id id=e.add(p,3,rup_processed,move(hints));++rup_processed;
            if(p.lits.empty())final_id=id;
            if(rup_processed%10000==0)cerr<<"processed "<<rup_processed<<" RUP records\n";
        }
        if(!final_id){
            if(!e.check({},hints))throw runtime_error("final empty clause is not unit-refutable");
            final_id=e.add({false,{}},3,-1,move(hints));
        }
        vector<unsigned char> keep(e.db.size(),0);vector<Id> todo{final_id};
        while(!todo.empty()){Id id=todo.back();todo.pop_back();if(keep[id])continue;keep[id]=1;
            if(!e.db[id].kind)throw runtime_error("null axiom in dependencies");
            for(Id reason:e.db[id].hints){if(reason<=0 || reason>=id)throw runtime_error("forward or invalid reason");todo.push_back(reason);}}
        ofstream trace(out/"trimmed_trace.jsonl");vector<int> selected_theories,selected_inputs;long kept=0,derived=0,hint_count=0;
        for(Id id=1;id<static_cast<Id>(e.db.size());++id)if(keep[id]){
            Clause const& c=e.db[id];++kept;
            if(c.kind==3){trace<<"{\"kind\":\"rup\",\"id\":"<<id<<",\"clause\":";ints(trace,c.lits);trace<<",\"reasons\":";ints(trace,c.hints);trace<<"}\n";++derived;hint_count+=c.hints.size();}
            else {trace<<"{\"kind\":\"axiom\",\"id\":"<<id<<",\"source\":\""<<(c.kind==1?"input":"theory")<<"\",\"source_index\":"<<c.source<<",\"clause\":";ints(trace,c.lits);trace<<"}\n";
                (c.kind==1?selected_inputs:selected_theories).push_back(c.source);}
        }
        trace.close();ofstream st(out/"selected_theory_indices.json");ints(st,selected_theories);st<<'\n';st.close();
        ofstream si(out/"selected_input_indices.json");ints(si,selected_inputs);si<<'\n';si.close();
        double seconds=chrono::duration<double>(chrono::steady_clock::now()-start).count();
        ofstream report(out/"producer_result.json");report<<"{\"status\":\"UNTRUSTED_RUP_DEPENDENCY_TRACE_PRODUCED\",\"input_records\":"<<input_count<<",\"theory_records\":"<<theory_count<<",\"base_clause_ids\":"<<base<<",\"rup_records_processed\":"<<rup_processed<<",\"final_empty_id\":"<<final_id<<",\"selected_input_count\":"<<selected_inputs.size()<<",\"selected_theory_count\":"<<selected_theories.size()<<",\"selected_derived_count\":"<<derived<<",\"trimmed_records\":"<<kept<<",\"ordered_reason_count\":"<<hint_count<<",\"unit_propagations\":"<<e.propagations<<",\"rup_checks\":"<<e.checks<<",\"seconds\":"<<seconds<<"}\n";report.close();
        if(!trace || !st || !si || !report)throw runtime_error("output write failed");
        for(auto const& name:{"trimmed_trace.jsonl","selected_theory_indices.json","selected_input_indices.json","producer_result.json"})sync_file(out/name);
        cerr<<"trace complete: "<<selected_theories.size()<<" theory clauses, "<<derived<<" derived clauses, "<<seconds<<" s\n";
        return 0;
    } catch(exception const& error){cerr<<"ERROR: "<<error.what()<<'\n';return 2;}
}
