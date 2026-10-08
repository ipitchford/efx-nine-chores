#!/usr/bin/env python3
"""Validate a prepared CPC stage; execute only with the explicit --execute flag.

Export and Ethos replay are separate stages. Neither automatically starts the
other. A hard wall guard kills the stage at its configured total budget.
"""
import argparse
from datetime import datetime,timezone
import hashlib,json,os,resource,signal,subprocess,time
from pathlib import Path


def sha(path):
    digest=hashlib.sha256()
    with Path(path).open('rb') as stream:
        for data in iter(lambda:stream.read(1<<20),b''):digest.update(data)
    return digest.hexdigest()


def atomic(path,data):
    temporary=path.with_suffix('.json.tmp')
    with temporary.open('w') as stream:
        json.dump(data,stream,indent=2);stream.write('\n');stream.flush();os.fsync(stream.fileno())
    temporary.replace(path)


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('configuration',type=Path)
    parser.add_argument('--stage',choices=['export','replay'],required=True)
    parser.add_argument('--execute',action='store_true')
    args=parser.parse_args();config=json.loads(args.configuration.read_text())
    assert sha(config['input'])==config['input_sha256']
    assert sha(config['runner'])==config['runner_sha256']
    replay=config['replay_argv'];replay_runner=Path(replay[1])
    assert sha(replay_runner)==config['replay_runner_sha256']
    checker=Path(replay[replay.index('--checker')+1]);signatures=Path(replay[replay.index('--signatures')+1])
    assert sha(checker)==config['ethos_binary_sha256']
    actual_signatures={str(p.relative_to(signatures)):sha(p) for p in sorted(signatures.rglob('*.eo'))}
    assert actual_signatures==config['signature_sha256']
    assert '--include-expert' not in replay
    if args.stage=='replay':
        verdict=json.loads(Path(config['verdict_file']).read_text())
        report=json.loads(Path(config['export_report']).read_text())
        assert verdict['result']==report['result']=='unsat'
        assert verdict['input_sha256']==report['input_sha256']==config['input_sha256']
        proof=next(p for p in report['proofs'] if p['format']=='cpc')
        assert Path(proof['path']).resolve()==Path(config['proof_file']).resolve()
        assert proof['sha256']==sha(config['proof_file']) and proof['trust_or_hole_steps']==0
    prefix='producer' if args.stage=='export' else 'replay'
    command=config['producer_argv'] if args.stage=='export' else config['replay_argv']
    budget=config['producer_supervisor_budget_seconds'] if args.stage=='export' else config.get('replay_supervisor_budget_seconds',1205)
    memory=config['producer_address_space_mib'] if args.stage=='export' else config['replay_address_space_mib']
    initial=dict(status='preflight_passed_not_executed',stage=args.stage,configuration_sha256=sha(args.configuration),
                 input_sha256=config['input_sha256'],command=command,hard_wall_seconds=budget,address_space_mib=memory)
    if not args.execute:print(json.dumps(initial,indent=2));return
    directory=Path(config['run_directory']);directory.mkdir(parents=True,exist_ok=True)
    started_file=directory/f'{prefix}_started.json'
    assert not started_file.exists(), 'Use a fresh prepared output prefix for a new attempt'
    if args.stage=='export':assert not Path(config['verdict_file']).exists()
    memory_stats={key:int(value) for key,value in (line.split() for line in Path('/sys/fs/cgroup/memory.stat').read_text().splitlines())}
    maximum=int(Path('/sys/fs/cgroup/memory.max').read_text())
    current=int(Path('/sys/fs/cgroup/memory.current').read_text())
    guarded_keys=('anon','kernel','shmem','file_mapped','file_dirty','file_writeback','sock')
    nonreclaimable=sum(memory_stats.get(key,0) for key in guarded_keys)
    reserve=int(config.get('other_work_reserve_mib',2048))*1024**2
    guard=dict(memory_max=maximum,memory_current=current,nominal_headroom=maximum-current,
        components={key:memory_stats.get(key,0) for key in guarded_keys},
        file_cache_bytes=memory_stats.get('file',0),active_file_bytes=memory_stats.get('active_file',0),
        inactive_file_bytes=memory_stats.get('inactive_file',0),
        conservative_nonreclaimable_estimate=nonreclaimable,other_work_reserve_bytes=reserve,
        requested_address_space_bytes=memory*1024**2,
        margin_bytes=maximum-nonreclaimable-reserve-memory*1024**2,
        rule='Count anon+kernel+shmem+mapped_file+dirty+writeback+sock conservatively; reserve other work and hard process cap. Clean unmapped page cache is reclaimable, including active cache.')
    atomic(directory/f'{prefix}_memory_guard.json',guard)
    assert guard['margin_bytes']>=0,'Insufficient memory under the conservative nonreclaimable-memory guard'
    initial.update(status='launching',utc=datetime.now(timezone.utc).isoformat(),memory_guard=guard,
        supervisor_sha256=sha(Path(__file__)))
    atomic(started_file,initial)
    def limit():
        resource.setrlimit(resource.RLIMIT_AS,(memory*1024**2,)*2)
        signal.signal(signal.SIGALRM,signal.SIG_DFL)
        signal.alarm(int(budget))
    began=time.monotonic();timed_out=False
    with (directory/f'{prefix}.log').open('w') as log:
        child=subprocess.Popen(command,cwd=config['working_directory'],stdout=log,stderr=subprocess.STDOUT,preexec_fn=limit,start_new_session=True)
        try:
            while child.poll() is None:
                remaining=budget-(time.monotonic()-began)
                if remaining<=0:
                    timed_out=True;os.killpg(child.pid,signal.SIGKILL);child.wait();break
                atomic(directory/f'{prefix}_heartbeat.json',dict(utc=datetime.now(timezone.utc).isoformat(),
                       elapsed=time.monotonic()-began,remaining=remaining,memory_current_bytes=int(Path('/sys/fs/cgroup/memory.current').read_text())))
                try:child.wait(timeout=min(5,remaining))
                except subprocess.TimeoutExpired:pass
        except BaseException:
            if child.poll() is None:os.killpg(child.pid,signal.SIGKILL);child.wait()
            raise
        finally:
            verdict_path=Path(config['verdict_file'])
            verdict=json.loads(verdict_path.read_text()) if verdict_path.exists() else None
            terminal=dict(status='hard_wall_timeout' if timed_out else 'child_completed',stage=args.stage,
                returncode=child.poll(),elapsed=time.monotonic()-began,input_sha256=config['input_sha256'],
                child_max_rss_kib=resource.getrusage(resource.RUSAGE_CHILDREN).ru_maxrss,finished_at_utc=datetime.now(timezone.utc).isoformat(),
                input_unchanged=sha(config['input'])==config['input_sha256'],
                durable_solver_verdict=verdict,
                scope='A solver verdict and an independently verified proof are separate outcomes.')
            atomic(directory/f'{prefix}_terminal.json',terminal);print(json.dumps(terminal),flush=True)


if __name__=='__main__':main()
