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
#include <limits>
#include <queue>
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
Parsed parse_clause(string const& line,string const& field="clause",bool canonical=true) {
    auto p=line.find("\""+field+"\"");
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
    if(canonical && (!is_sorted(out.lits.begin(),out.lits.end()) || adjacent_find(out.lits.begin(),out.lits.end())!=out.lits.end()))
        throw runtime_error("capture clause is not canonical");
    if(canonical)for(int x:out.lits)if(binary_search(out.lits.begin(),out.lits.end(),-x))throw runtime_error("tautological capture clause");
    return out;
}
Id parse_id(string const& line) {
    auto p=line.find("\"id\"");if(p==string::npos)throw runtime_error("checkpoint missing ID");
    p=line.find(':',p);if(p==string::npos)throw runtime_error("checkpoint missing colon");
    char* end=nullptr;long value=strtol(line.c_str()+p+1,&end,10);
    if(end==line.c_str()+p+1 || value<=0 || value>2000000000L)throw runtime_error("bad checkpoint ID");
    return static_cast<Id>(value);
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
    vector<Id> base_units;
    vector<unsigned> assumption_stamp;
    unsigned current_assumption_stamp=0;
    vector<int> trail;
    vector<Id> ordered;
    vector<unsigned> needed;
    unsigned stamp=0;
    Id empty_axiom=0;
    Id prefix_limit=numeric_limits<Id>::max();
    Id source_cache_end=0;
    vector<pair<Id,int>> reduced_units;
    unordered_map<int,Id> first_reduced_unit;
    Id first_reduced_conflict=0;
    Id base_conflict=0;
    size_t base_trail_size=0;
    bool base_initialized=false;
    long propagations=0,checks=0;
    void ensure(int v) {
        if(static_cast<int>(values.size())<=v){values.resize(v+1,0);reasons.resize(v+1,0);base_units.resize(v+1,0);assumption_stamp.resize(v+1,0);watches.resize(2*(v+1)+2);}
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
        else {
            if(base_initialized){
                vector<int> positions;
                for(int j=0;j<static_cast<int>(p.lits.size());++j)if(val(p.lits[j])!=-1)positions.push_back(j);
                for(int j=0;positions.size()<2 && j<static_cast<int>(p.lits.size());++j)
                    if(find(positions.begin(),positions.end(),j)==positions.end())positions.push_back(j);
                db[id].w0=positions[0];db[id].w1=positions[1];
            }
            watches[wi(p.lits[db[id].w0])].push_back(id);watches[wi(p.lits[db[id].w1])].push_back(id);
        }
        return id;
    }
    vector<Id> base_conflict_hints(Id conflict) {
        vector<Id> result;
        for(int lit:db[conflict].lits){
            if(val(lit)!=-1 || !base_units[abs(lit)])throw runtime_error("invalid permanent conflict");
            result.push_back(base_units[abs(lit)]);
        }
        result.push_back(conflict);return result;
    }
    void assign_base(int lit,Id reason) {
        if(val(lit)!=0)throw runtime_error("permanent assignment is not fresh");
        Id unit=reason;
        if(db[reason].lits.size()!=1){
            vector<Id> hints;
            for(int other:db[reason].lits)if(other!=lit){
                if(val(other)!=-1 || !base_units[abs(other)])throw runtime_error("nonunit permanent reason");
                hints.push_back(base_units[abs(other)]);
            }
            hints.push_back(reason);
            unit=add({false,{lit}},3,-2,move(hints));
        }
        assign(lit,unit);base_units[abs(lit)]=unit;base_trail_size=trail.size();
    }
    Id propagate(size_t head,bool permanent) {
        while(head<trail.size()) {
            int false_lit=-trail[head++];++propagations;
            auto& list=watches[wi(false_lit)];size_t k=0;
            while(k<list.size()) {
                Id id=list[k];
                if(!permanent && id>=prefix_limit){list[k]=list.back();list.pop_back();continue;}
                Clause& c=db[id];
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
                if(val(other)==-1)return id;
                if(permanent)assign_base(other,id);
                else {ordered.push_back(id);assign(other,id);}
                ++k;
            }
        }
        return 0;
    }
    void initialize_base() {
        base_initialized=true;
        if(empty_axiom){base_conflict=empty_axiom;return;}
        // Only original unit axioms are queued here. Derived permanent units
        // are added during propagation and are already assigned at creation.
        size_t originals=units.size();
        for(size_t j=0;j<originals;++j){Id id=units[j];int lit=db[id].lits[0];
            if(val(lit)==-1){base_conflict=id;return;}
            if(!val(lit))assign_base(lit,id);
        }
        base_conflict=propagate(0,true);
    }
    void extend_base_from(Id id) {
        if(base_conflict)return;
        int only=0,count=0;
        for(int lit:db[id].lits){if(val(lit)==1)return;if(!val(lit)){only=lit;++count;}}
        if(count==0){base_conflict=id;return;}
        if(count>1)return;
        size_t head=base_trail_size;assign_base(only,id);base_conflict=propagate(head,true);
    }
    void index_provisional_under_source_cache(Id id) {
        int only=0,count=0;
        for(int lit:db[id].lits){if(val(lit)==1)return;if(!val(lit)){only=lit;++count;}}
        if(!count){if(!first_reduced_conflict)first_reduced_conflict=id;return;}
        if(count==1 && first_reduced_unit.emplace(only,id).second)reduced_units.push_back({id,only});
    }
    vector<Id> conflict_slice(Id conflict) {
        ++stamp;if(!stamp){fill(needed.begin(),needed.end(),0);++stamp;}
        vector<int> todo;vector<Id> permanent_hints;needed[conflict]=stamp;
        for(int lit:db[conflict].lits){if(val(lit)!=-1)throw runtime_error("conflict clause not false");todo.push_back(abs(lit));}
        while(!todo.empty()) {
            int v=todo.back();todo.pop_back();Id id=reasons[v];
            if(base_units[v]){
                if(assumption_stamp[v]!=current_assumption_stamp && needed[base_units[v]]!=stamp){
                    needed[base_units[v]]=stamp;permanent_hints.push_back(base_units[v]);
                }
                continue;
            }
            if(!id || needed[id]==stamp)continue;
            needed[id]=stamp;
            for(int lit:db[id].lits)if(abs(lit)!=v){
                if(val(lit)!=-1)throw runtime_error("reason dependency not false");
                todo.push_back(abs(lit));
            }
        }
        sort(permanent_hints.begin(),permanent_hints.end());
        vector<Id> result=move(permanent_hints);for(Id id:ordered)if(needed[id]==stamp)result.push_back(id);
        if(result.empty() || result.back()!=conflict)throw runtime_error("missing final conflict reason");
        return result;
    }
    bool check(vector<int> const& candidate,vector<Id>& hint) {
        ++checks;ordered.clear();
        for(int lit:candidate)ensure(abs(lit));
        if(base_conflict){hint=base_conflict_hints(base_conflict);return true;}
        for(int lit:candidate)if(val(lit)==1 && base_units[abs(lit)]){hint={base_units[abs(lit)]};return true;}
        ++current_assumption_stamp;
        if(!current_assumption_stamp){fill(assumption_stamp.begin(),assumption_stamp.end(),0);++current_assumption_stamp;}
        auto reset=[&](){for(size_t j=base_trail_size;j<trail.size();++j){int lit=trail[j];values[abs(lit)]=0;reasons[abs(lit)]=0;}trail.resize(base_trail_size);};
        auto finish=[&](Id conflict){ordered.push_back(conflict);hint=conflict_slice(conflict);reset();return true;};
        for(int lit:candidate){assumption_stamp[abs(lit)]=current_assumption_stamp;if(val(-lit)==-1)throw runtime_error("tautological RUP candidate");if(val(-lit)==0)assign(-lit,0);}
        if(empty_axiom && empty_axiom<prefix_limit)return finish(empty_axiom);
        if(first_reduced_conflict && first_reduced_conflict<prefix_limit)return finish(first_reduced_conflict);
        while(!reduced_units.empty() && reduced_units.back().first>=prefix_limit)reduced_units.pop_back();
        for(auto [id,lit]:reduced_units){
            if(val(lit)==-1)return finish(id);
            if(!val(lit)){ordered.push_back(id);assign(lit,id);}
        }
        Id conflict=propagate(base_trail_size,false);if(conflict)return finish(conflict);
        reset();hint.clear();return false;
    }
};
int main(int argc,char**argv) {
    try {
        if(argc!=3 && argc!=4)throw runtime_error("usage: rup_dependency_producer CAPTURE OUT_DIRECTORY [UNTRUSTED_CANDIDATE_CHECKPOINT]");
        filesystem::path capture=argv[1],out=argv[2];
        if(filesystem::exists(out))throw runtime_error("use a fresh output directory");
        filesystem::create_directories(out);
        auto start=chrono::steady_clock::now();Engine e;long input_count=0,theory_count=0,rup_processed=0;
        auto load=[&](string const& name,int kind,long& count){
            ifstream f(capture/name);if(!f)throw runtime_error("cannot read "+name);string line;
            while(getline(f,line)){Parsed p=parse_clause(line);if(kind==2 && p.is_null)throw runtime_error("null theory");e.add(p,kind,count++);}
        };
        load("input_clauses.jsonl",1,input_count);load("theory_clauses.jsonl",2,theory_count);
        Id base=e.db.size()-1,final_id=0;vector<Id> hints;string failure;
        // Cache only source-axiom consequences, before provisional RUP nodes
        // are admitted. These explicit unit proofs precede every RUP goal.
        e.initialize_base();e.source_cache_end=e.db.size()-1;
        Id cache_count=e.source_cache_end-base;
        cerr<<"source-only closure: "<<e.base_trail_size<<" fixed variables; "<<cache_count<<" derived unit nodes\n";
        // Captured RUP records enter provisionally. They are NOT accepted
        // axioms: every selected record must later be justified from the
        // strict earlier prefix, recursively, before any refutation is emitted.
        ifstream stream(capture/"rup_clauses.jsonl");if(!stream)throw runtime_error("missing RUP stream");string line;
        while(getline(stream,line)) {
            Parsed p=parse_clause(line);if(p.is_null)throw runtime_error("null RUP record");
            Id added=e.add(p,3,rup_processed);e.index_provisional_under_source_cache(added);++rup_processed;
            if(rup_processed%250000==0)cerr<<"loaded "<<rup_processed<<" provisional RUP records\n";
        }
        e.prefix_limit=e.db.size();
        if(!e.check({},hints))failure="final empty clause is not unit-refutable from captured records";
        else final_id=e.add({false,{}},3,-1,move(hints));
        long justified=0,resumed=0;
        vector<unsigned char> checked(e.db.size(),0);
        vector<unsigned char> expanded(e.db.size(),0);
        for(Id id=base+1;id<=e.source_cache_end;++id){checked[id]=expanded[id]=1;}
        // Checkpoints retain v6's captured-RUP IDs. Cached source-unit nodes
        // use the otherwise unused external IDs above all captured RUP IDs.
        auto external_id=[&](Id id)->Id{
            if(id<=base)return id;
            if(id<=e.source_cache_end)return base+rup_processed+(id-base);
            return id-cache_count;
        };
        auto internal_id=[&](Id id)->Id{
            if(id<=base)return id;
            if(id<=base+rup_processed)return id+cache_count;
            if(id<=base+rup_processed+cache_count)return base+(id-base-rup_processed);
            throw runtime_error("checkpoint ID exceeds known source ranges");
        };
        filesystem::path checkpoint_path=out/"candidate_justifications.jsonl";
        ofstream checkpoint(checkpoint_path);
        auto write_checkpoint=[&](Id id){
            Clause const& c=e.db[id];
            vector<Id> external_hints;for(Id reason:c.hints)external_hints.push_back(external_id(reason));
            checkpoint<<"{\"kind\":\"rup\",\"id\":"<<external_id(id)<<",\"clause\":";ints(checkpoint,c.lits);
            checkpoint<<",\"reasons\":";ints(checkpoint,external_hints);checkpoint<<"}\n";
        };
        for(Id id=base+1;id<=e.source_cache_end;++id)write_checkpoint(id);
        checkpoint.flush();sync_file(checkpoint_path);
        if(argc==4){
            ifstream previous(argv[3]);if(!previous)throw runtime_error("cannot open candidate checkpoint");
            string record;
            while(getline(previous,record)){
                if(previous.eof()){cerr<<"ignored unterminated final checkpoint line\n";break;}
                Id id=internal_id(parse_id(record));Parsed c=parse_clause(record),h=parse_clause(record,"reasons",false);
                if(id>base && id<=e.source_cache_end){
                    if(c.is_null || c.lits!=e.db[id].lits)throw runtime_error("source-unit checkpoint differs from fresh derivation");
                    continue; // Always use the freshly source-derived proof.
                }
                if(id<=base || id>=final_id || c.is_null || h.is_null || checked[id] || c.lits!=e.db[id].lits || h.lits.empty())throw runtime_error("invalid checkpoint record");
                for(Id& reason:h.lits)reason=internal_id(reason);
                for(Id reason:h.lits)if(reason<=0 || reason>=id)throw runtime_error("checkpoint has non-prefix dependency");
                e.db[id].hints=move(h.lits);checked[id]=1;++resumed;write_checkpoint(id);
            }
            checkpoint.flush();sync_file(checkpoint_path);
        }
        priority_queue<Id> required;
        if(final_id){checked[final_id]=1;for(Id id:e.db[final_id].hints)required.push(id);}
        Id previous_goal=e.db.size();
        while(!required.empty() && failure.empty()){
            Id id=required.top();required.pop();
            if(id<=base || expanded[id])continue;
            if(id>=previous_goal)throw runtime_error("goal thresholds are not strictly decreasing");
            previous_goal=id;
            e.prefix_limit=id;
            if(!checked[id]){
                auto same=e.identical.find(e.db[id].lits);
                if(same!=e.identical.end() && same->second<id)hints={same->second};
                else if(!e.check(e.db[id].lits,hints)){
                    failure="required RUP is not derivable from its strict earlier prefix at source index "+to_string(e.db[id].source);
                    break;
                }
                for(Id reason:hints)if(reason<=0 || reason>=id)throw runtime_error("non-prefix dependency");
                e.db[id].hints=move(hints);checked[id]=1;++justified;write_checkpoint(id);
            }
            expanded[id]=1;
            for(Id reason:e.db[id].hints)if(reason>base && !expanded[reason])required.push(reason);
            if(justified && justified%1000==0){
                checkpoint.flush();sync_file(checkpoint_path);
                cerr<<"justified "<<justified<<" new required RUP records; resumed "<<resumed<<"; pending "<<required.size()<<'\n';
            }
        }
        checkpoint.flush();checkpoint.close();sync_file(checkpoint_path);
        if(!failure.empty()){
            ofstream partial(out/"producer_result.json");
            partial<<"{\"status\":\"UNTRUSTED_BACKWARD_EXTRACTION_INCOMPLETE_NO_REFUTATION\",\"failure\":\""<<failure<<"\",\"input_records\":"<<input_count<<",\"theory_records\":"<<theory_count<<",\"provisional_rup_records\":"<<rup_processed<<",\"required_rup_records_justified\":"<<justified<<",\"final_empty_id\":0}\n";
            partial.close();sync_file(out/"producer_result.json");
            cerr<<"NO REFUTATION: "<<failure<<'\n';return 3;
        }
        cerr<<"backward justification complete: "<<justified<<" required RUP records\n";
        vector<unsigned char> keep(e.db.size(),0);vector<Id> todo;
        if(final_id)todo.push_back(final_id);
        else for(Id id=base+1;id<static_cast<Id>(e.db.size());++id)todo.push_back(id);
        while(!todo.empty()){Id id=todo.back();todo.pop_back();if(keep[id])continue;keep[id]=1;
            if(!e.db[id].kind)throw runtime_error("null axiom in dependencies");
            if(id>base && !checked[id])throw runtime_error("unjustified provisional clause reached final proof");
            for(Id reason:e.db[id].hints){if(reason<=0 || reason>=id)throw runtime_error("forward or invalid reason");todo.push_back(reason);}}
        string trace_name=final_id?"trimmed_trace.jsonl":"valid_prefix_trace.jsonl";
        ofstream trace(out/trace_name);vector<int> selected_theories,selected_inputs;long kept=0,derived=0,hint_count=0;
        for(Id id=1;id<static_cast<Id>(e.db.size());++id)if(keep[id]){
            Clause const& c=e.db[id];++kept;
            if(c.kind==3){trace<<"{\"kind\":\"rup\",\"id\":"<<id<<",\"clause\":";ints(trace,c.lits);trace<<",\"reasons\":";ints(trace,c.hints);trace<<"}\n";++derived;hint_count+=c.hints.size();}
            else {trace<<"{\"kind\":\"axiom\",\"id\":"<<id<<",\"source\":\""<<(c.kind==1?"input":"theory")<<"\",\"source_index\":"<<c.source<<",\"clause\":";ints(trace,c.lits);trace<<"}\n";
                (c.kind==1?selected_inputs:selected_theories).push_back(c.source);}
        }
        trace.close();ofstream st(out/"selected_theory_indices.json");ints(st,selected_theories);st<<'\n';st.close();
        ofstream si(out/"selected_input_indices.json");ints(si,selected_inputs);si<<'\n';si.close();
        double seconds=chrono::duration<double>(chrono::steady_clock::now()-start).count();
        ofstream report(out/"producer_result.json");report<<"{\"status\":\""<<(final_id?"UNTRUSTED_RUP_DEPENDENCY_TRACE_PRODUCED":"UNTRUSTED_RUP_PREFIX_ONLY_NO_REFUTATION")<<"\",\"failure\":\""<<failure<<"\",\"input_records\":"<<input_count<<",\"theory_records\":"<<theory_count<<",\"base_clause_ids\":"<<base<<",\"rup_records_processed\":"<<rup_processed<<",\"final_empty_id\":"<<final_id<<",\"selected_input_count\":"<<selected_inputs.size()<<",\"selected_theory_count\":"<<selected_theories.size()<<",\"selected_derived_count\":"<<derived<<",\"trimmed_records\":"<<kept<<",\"ordered_reason_count\":"<<hint_count<<",\"unit_propagations\":"<<e.propagations<<",\"rup_checks\":"<<e.checks<<",\"seconds\":"<<seconds<<"}\n";report.close();
        if(!trace || !st || !si || !report)throw runtime_error("output write failed");
        for(auto const& name:vector<string>{trace_name,"selected_theory_indices.json","selected_input_indices.json","producer_result.json"})sync_file(out/name);
        cerr<<"trace complete: "<<selected_theories.size()<<" theory clauses, "<<derived<<" derived clauses, "<<seconds<<" s\n";
        if(!final_id){cerr<<"NO REFUTATION: "<<failure<<'\n';return 3;}
        return 0;
    } catch(exception const& error){cerr<<"ERROR: "<<error.what()<<'\n';return 2;}
}
