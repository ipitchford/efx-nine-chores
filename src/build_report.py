#!/usr/bin/env python3
"""Build the research memorandum with ReportLab and vector mathematical type.

The report explicitly distinguishes the unresolved target from supported
ancillary results. Its editable textual counterpart is written alongside it.
"""
from pathlib import Path
import collections
import io
import json
import re

import matplotlib
matplotlib.use('Agg')
matplotlib.rcParams['svg.fonttype'] = 'path'
from matplotlib.mathtext import math_to_image
from matplotlib.font_manager import FontProperties
from svglib.svglib import svg2rlg
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.pagesizes import A4
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import (BaseDocTemplate, PageTemplate, Frame, Paragraph,
    Spacer, Table, TableStyle, PageBreak, KeepTogether, Preformatted)

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'output' / 'pdf'
OUT.mkdir(parents=True, exist_ok=True)
TMP = ROOT / 'tmp' / 'pdfs'
TMP.mkdir(parents=True, exist_ok=True)
PDF = OUT / 'economics-problem-2-research-report.pdf'
MD = ROOT / 'docs' / 'research_report.md'

for name, file in [('Body','DejaVuSerif.ttf'), ('BodyBold','DejaVuSerif-Bold.ttf'),
                   ('Head','DejaVuSans.ttf'), ('HeadBold','DejaVuSans-Bold.ttf'),
                   ('Code','DejaVuSansMono.ttf')]:
    pdfmetrics.registerFont(TTFont(name, '/usr/share/fonts/truetype/dejavu/'+file))
pdfmetrics.registerFontFamily('Body', normal='Body', bold='BodyBold', italic='Body', boldItalic='BodyBold')
pdfmetrics.registerFontFamily('Head', normal='Head', bold='HeadBold', italic='Head', boldItalic='HeadBold')

INK = colors.HexColor('#192D38')
TEAL = colors.HexColor('#19656A')
GREY = colors.HexColor('#52626B')
LIGHT = colors.HexColor('#EDF3F3')
AMBER = colors.HexColor('#FFF3D9')
LINE = colors.HexColor('#CAD5D8')
W, H = A4
MARGIN = 54
WIDTH = W - 2*MARGIN

styles = {
 'body': ParagraphStyle('body', fontName='Body', fontSize=9.5, leading=14,
                        textColor=INK, spaceAfter=8),
 'small': ParagraphStyle('small', fontName='Head', fontSize=8, leading=11,
                         textColor=GREY, spaceAfter=6),
 'h1': ParagraphStyle('h1', fontName='HeadBold', fontSize=15, leading=19,
                      textColor=TEAL, spaceBefore=16, spaceAfter=9, keepWithNext=True),
 'h2': ParagraphStyle('h2', fontName='HeadBold', fontSize=11, leading=15,
                      textColor=INK, spaceBefore=10, spaceAfter=6, keepWithNext=True),
 'title': ParagraphStyle('title', fontName='HeadBold', fontSize=28, leading=33,
                         textColor=INK, spaceAfter=16),
 'sub': ParagraphStyle('sub', fontName='Head', fontSize=13, leading=18,
                       textColor=GREY, spaceAfter=18),
 'cell': ParagraphStyle('cell', fontName='Head', fontSize=8, leading=11,
                        textColor=INK, spaceAfter=0),
 'cellhead': ParagraphStyle('cellhead', fontName='HeadBold', fontSize=8,
                            leading=11, textColor=colors.white, spaceAfter=0),
 'code': ParagraphStyle('code', fontName='Code', fontSize=7.2, leading=10,
                        textColor=INK, backColor=LIGHT, borderPadding=9,
                        spaceBefore=5, spaceAfter=8),
}
story, markdown = [], []

def para(text, small=False):
    story.append(Paragraph(text, styles['small' if small else 'body']))
    markdown.append(text+'\n')

def heading(text, level=1):
    story.append(Paragraph(text, styles['h1' if level==1 else 'h2']))
    markdown.append('#'*(level+1)+' '+text+'\n')

def eq(formula):
    buffer = io.BytesIO()
    math_to_image('$'+formula+'$', buffer, format='svg',
                  prop=FontProperties(size=12), color='#192D38')
    drawing = svg2rlg(io.BytesIO(buffer.getvalue()))
    factor = min(1.0, (WIDTH-18)/drawing.width)
    drawing.scale(factor,factor)
    drawing.width *= factor
    drawing.height *= factor
    drawing.hAlign='CENTER'
    story.extend([Spacer(1,3),drawing,Spacer(1,11)])
    markdown.append('$$\n'+formula+'\n$$\n')

def table(headers, rows, fractions=None, keep=False):
    widths = [WIDTH*x for x in fractions] if fractions else [WIDTH/len(headers)]*len(headers)
    data = [[Paragraph(str(x), styles['cellhead']) for x in headers]]
    data.extend([[Paragraph(str(x),styles['cell']) for x in row] for row in rows])
    item = Table(data,colWidths=widths,repeatRows=1,hAlign='LEFT')
    item.setStyle(TableStyle([
      ('BACKGROUND',(0,0),(-1,0),TEAL),('VALIGN',(0,0),(-1,-1),'TOP'),
      ('LEFTPADDING',(0,0),(-1,-1),7),('RIGHTPADDING',(0,0),(-1,-1),7),
      ('TOPPADDING',(0,0),(-1,-1),7),('BOTTOMPADDING',(0,0),(-1,-1),7),
      ('ROWBACKGROUNDS',(0,1),(-1,-1),[colors.white,LIGHT]),
      ('LINEBELOW',(0,-1),(-1,-1),0.5,LINE)]))
    story.extend([KeepTogether([item]) if keep else item,Spacer(1,11)])
    clean=lambda x: re.sub('<[^>]+>','',str(x)).replace('|','/')
    markdown.append('| '+' | '.join(map(clean,headers))+' |\n| '+' | '.join(['---']*len(headers))+' |\n'+
                    '\n'.join('| '+' | '.join(map(clean,row))+' |' for row in rows)+'\n')

def code(text):
    story.append(Preformatted(text,styles['code']))
    markdown.append('```sh\n'+text+'\n```\n')

def page(force=False):
    if force or not any(isinstance(item,PageBreak) for item in story):
        story.append(PageBreak())
    markdown.append('\n')

def json_read(path):
    p=ROOT/path
    return json.loads(p.read_text()) if p.exists() else None

p7receipt = json_read('results/designated7_core_ethos.json')
p7verified = bool(p7receipt and p7receipt.get('result')=='verified' and p7receipt.get('reference_binding'))
continuation_status = json_read('docs/CONTINUATION_STATUS.json') or {}
assert continuation_status.get('main_status','unresolved') == 'unresolved', 'A resolving result requires a revised theorem manuscript.'

story.append(Spacer(1,25))
story.append(Paragraph('Nine chores for<br/>three agents',styles['title']))
story.append(Paragraph('Exact finite bounds, checked certificates,<br/>and the unresolved nine-chore question',styles['sub']))
para('Research memorandum for consideration by Evidence Press<br/>7 October 2026',small=True)
markdown.insert(0,'# Nine chores for three agents\n\nResearch memorandum for consideration by Evidence Press. 7 October 2026.\n')
notice=Table([[Paragraph('<b>Status of Problem 2: unresolved.</b> This investigation has produced neither a universal nine-chore existence proof nor a nine-chore counterexample. The results below must not be released as a solution of that question.',styles['body'])]],colWidths=[WIDTH])
notice.setStyle(TableStyle([('BACKGROUND',(0,0),(-1,-1),AMBER),('BOX',(0,0),(-1,-1),0.5,colors.HexColor('#D6B667')),('LEFTPADDING',(0,0),(-1,-1),12),('RIGHTPADDING',(0,0),(-1,-1),12),('TOPPADDING',(0,0),(-1,-1),12),('BOTTOMPADDING',(0,0),(-1,-1),5)]))
story.extend([Spacer(1,15),notice,Spacer(1,18)])
markdown.append('**Status of Problem 2: unresolved.** Neither a universal existence proof nor a nine-chore counterexample was obtained.\n')
heading('What this record establishes')
para('The target is complete envy-free-up-to-any-chore allocation (EFX) for three agents and nine indivisible chores with arbitrary nonnegative additive costs. Every owned chore, including a zero-cost chore, remains in the removal quantifier. There are 19,683 complete labelled allocations.')
para('<b>A smaller exact search is now justified:</b> a counterexample, if one exists, survives setting one cheapest chore per row to zero. Independent scaling then leaves only <b>21 free real variables</b>. A complete finite representative has one zero per row and every other cost an integer from 1 to <b>3,831</b>. A positive representative has all row minima exactly 1 and every other cost even and at most <b>7,662</b>. These domains have not been exhausted. Two further methods give exact certificates for sufficient families; their global coverage remains unproved.')
para('The earlier work supplies an eight-chore obstruction to requiring a prescribed agent also to be ordinarily envy-free: all 6,561 allocations are checked, with 36 EFX allocations and no witness for that prescribed agent. The stronger property is proved for six chores using an externally checked arithmetic refutation. The ordinary seven-chore residual is checked in the same way. These results retain their separate scopes.')
para('The accompanying archive contains the complete mathematical arguments, exact inputs and certificates, independent checking code, source and version pins, run receipts, and a claim-by-claim evidence record. It preserves unsuccessful outcomes as unsuccessful outcomes.',small=True)

page()
heading('1. The exact question and the current frontier')
para('Let the agents be 0, 1 and 2, and let M contain nine chores. Costs add over bundles. A complete labelled allocation partitions M into A<sub>0</sub>, A<sub>1</sub> and A<sub>2</sub>; an empty bundle is permitted. The question asks whether such a partition always exists with')
eq(r'c_i(A_i\setminus\{g\})\leq c_i(A_j)\quad(i\ne j,\ g\in A_i).')
para('Each comparison uses only the evaluating agent\'s row, on both sides. No item may be discarded, divided or fractionally assigned. No approximation or cost ceiling is part of the question.')
para('For a nonempty bundle S, the largest remaining cost after deleting one owned chore is its total cost minus its cheapest owned chore. Define the residual of an empty bundle as zero. Then')
eq(r'r_i(S)=c_i(S)-\min_{g\in S}c_i(g),\qquad r_i(\varnothing)=0.')
para('EFX is equivalent to requiring each own residual to be at most the cost of each other bundle. The empty-bundle convention agrees with the original vacuous deletion condition because all comparison costs are nonnegative. In particular, deleting a zero-cost chore can leave the whole cost unchanged; omitting that deletion weakens the problem.')
para('Zhang\'s inspected version 2, dated 6 October 2026, establishes EFX existence for seven and eight chores and explicitly leaves nine chores open. It also states the shared-minimum reduction for nine chores in Section 6. Those conclusions and reductions are prior work, not new results of this investigation [1]. Kobayashi, Mahara and Sakamoto supply the earlier small-instance theorem and minimum-insertion method [2].')
heading('The two acceptable ways to settle the target',2)
para('A negative solution requires a rational 3 by 9 matrix and a proof that all 19,683 complete allocations violate EFX. A positive solution requires an argument covering every nonnegative real matrix. An arbitrary integer cutoff does not suffice; a proved complete representative bound, such as Section 9, would justify an exhaustive negative result. The required exhaustive result has not been obtained.')

heading('2. Exact reduction to linear arithmetic')
para('For a fixed complete allocation a, let Bad<sup>EFX</sup><sub>a</sub>(C) mean that at least one EFX comparison fails strictly:')
eq(r'\operatorname{Bad}^{\mathrm{EFX}}_a(C)=\bigvee_{i\ne j,\ g\in A_i(a)}\left[c_i(A_i(a)\setminus\{g\})>c_i(A_j(a))\right].')
para('The exact counterexample formula is the conjunction of that failure assertion over every allocation:')
eq(r'\Phi_9(C)=\bigwedge_{a\in\{0,1,2\}^{9}}\operatorname{Bad}^{\mathrm{EFX}}_a(C),\qquad C\geq0.')
para('There are 27 real cost variables. Every allocation-failure atom is a strict linear inequality, so the formula belongs to quantifier-free linear real arithmetic. A satisfying model is a counterexample. A correctly encoded, checked refutation supplies the finite computational part of a universal existence proof. A timeout or process failure supplies neither conclusion.')
heading('Why generic, positive instances suffice',2)
para('Suppose a counterexample exists. Choose one strict failed comparison for each of its finitely many allocations. All chosen margins remain positive in a sufficiently small neighbourhood. Within that neighbourhood, choose positive rational costs avoiding all within-row equality hyperplanes. The same allocation failures persist. This proves that a real counterexample, if one exists, has a positive rational representative; clearing denominators gives positive integers without imposing any upper bound.')
para('The argument also justifies strict item orders in residual searches. It is a standard perturbation idea; Yin and Mehta give an explicit earlier perturbation for chores EFX in Lemma 2.1 [3]. It does not independently decide the target. Positive row scaling and simultaneous chore permutations preserve all the comparisons.')
heading('What the residual search omits, and why',2)
para('A chore cheapest for two agents can be deleted; the known eight-chore EFX theorem and the KMS insertion lemma then extend an EFX allocation back to nine chores. Consequently a generic nine-chore counterexample must have three distinct cheapest chores. Relabel these as each agent\'s pinned minimum, and sort the six remaining chores by agent 0\'s cost. An interchange of agents 1 and 2, with their pinned chores, removes one further symmetry. This nine-chore reduction is already in Zhang\'s paper [1, Section 6].')
para('With positive costs and more than three chores, an EFX allocation cannot have an empty bundle: some other agent owns at least two chores, and its positive residual exceeds the empty bundle\'s zero cost. Thus the reduced formula needs only the surjective allocations:')
eq(r'3^9-3\cdot2^9+3=18\,150.')
para('The positive-domain omission is never applied directly to arbitrary zero-cost instances. The handwritten perturbation and relabelling argument connects those instances to the reduced search. Checking the resulting arithmetic refutation would not, by itself, formalise that connection.')

page()
heading('3. A stronger induction property and its limitation')
para('Write P<sub>m</sub> for the following stronger assertion: every three-agent m-chore instance admits an EFX allocation in which any <b>prescribed</b> agent p is also ordinarily envy-free. Ordinary envy-freeness means')
eq(r'c_p(A_p)\leq c_p(A_j)\quad(j\ne p).')
para('The agent must be specified in advance. A guarantee that <i>some</i> agent receives a cheapest bundle has a different quantifier and is insufficient for this property.')
heading('Insertion into an envy-free owner',2)
para('<b>Lemma.</b> If P<sub>m</sub> holds, then ordinary EFX exists for every three-agent instance with m+1 chores. Choose a cheapest chore e for p and delete it. Obtain a P<sub>m</sub> allocation, then add e to p\'s own bundle. Because e is cheapest, the new residual equals the old total (also when the old bundle was empty). That old total was no greater than either other bundle\'s cost. Every other agent retains its own bundle and sees another bundle weakly increase. All EFX inequalities follow.')
para('This makes P<sub>8</sub> a sufficient route to the requested nine-chore theorem. Section 4 gives an exact counterexample to P<sub>8</sub>, so that proposed route does not prove universal nine-chore existence.')
heading('A preservation lemma for any number of agents',2)
para('<b>Lemma.</b> Suppose an EFX allocation already makes prescribed agent p ordinarily envy-free. An additional chore e can be inserted while preserving both properties if e is cheapest among all chores for every agent other than p. This statement permits zero costs and empty bundles. It refines the KMS minimum-insertion argument by maintaining the prescribed agent\'s additional invariant; priority for the refinement is not claimed.')
para('<b>Proof.</b> For each agent other than p, point to the current owner of one of that agent\'s minimum-cost bundles. Give p no outgoing arc. If a directed cycle exists, it excludes p. Rotate the bundles along the cycle, so every cycle agent receives a minimum-cost bundle. Add e to one cycle agent\'s new bundle B. Its residual becomes c<sub>i</sub>(B), which is at most every other bundle cost. Others keep EFX, and p keeps its old minimum-cost bundle.')
para('If no directed cycle exists, every path ends at p. First add e to p\'s bundle. If p remains ordinarily envy-free, the allocation works. Otherwise choose a new minimum-cost bundle A<sub>j</sub> for p, and follow the path from j to p. Give A<sub>j</sub> to p, give each intermediate agent the original minimum-cost bundle to which it points, and give the original A<sub>p</sub> together with e to the last agent on the path. Each intermediate agent receives an original minimum-cost bundle; the collection of bundle totals has only weakly increased. The last agent\'s residual is the old cost of A<sub>p</sub>, which it regarded as minimum. Agents outside the path keep their old bundles. This proves every required inequality, including the case of an empty old bundle.')
para('A separately implemented finite check exercises this construction on all 512 binary 3 by 3 cost matrices, all 4,032 suitable starting allocations, and 9,846 admissible binary insertions. The general proof is the preceding cycle/path argument; these finite checks audit its implementation.')
heading('The six-chore result and the seven-chore dependency',2)
para('<b>Computer-assisted result.</b> P<sub>6</sub> holds. If the prescribed row is zero, give it everything. If another row is zero, give p a cheapest singleton, give the third agent another singleton, and give the zero-cost agent the remaining chores. Both other bundles are nonempty, so p is ordinarily envy-free. For nonzero rows, normalise row totals to one and lexicographically sort columns.')
para('For these canonical costs, conjoin the failure of every possible P<sub>6</sub> allocation. A failure is either ordinary envy by agent 0 or an EFX violation by agent 1 or 2. The resulting static input has 18 real variables and 755 assertions, including all 729 allocation clauses. cvc5 refutes it and exports a CPC proof; Ethos independently checks that proof against the exact input. This closes the finite arithmetic step, subject to the stated encoding and checker trust boundary. Padding with zero-cost dummy chores extends the positive result to every smaller cardinality.')
para('For seven chores, the preservation lemma handles instances where the two nonprescribed agents share a cheapest chore. After generic perturbation, the remainder has two distinct pinned minima and 1,806 nonempty allocation clauses. Z3 returned UNSAT for this 1,847-assertion residual in 99.72 seconds. The associated independent certificate status is '+('now verified; its receipt and exact selected input are in the archive.' if p7verified else '<b>not obtained</b>. The first cvc5 attempt exhausted its imposed memory limit without a verdict. A separate run on an 853-assertion subset exited with code 139 before emitting any verdict or certificate; its cause was not established.')+' The mathematical reduction is fully written in the accompanying ancillary proof record.')

page(force=True)
heading('4. An exact eight-chore obstruction')
para('Use the following positive integer costs. Chores are labelled g<sub>1</sub> through g<sub>8</sub> in this memorandum. Reproduction code uses indices 0 through 7 for the same columns.')
from verify_finite import P8_MATRIX
table(['Agent']+['g'+str(i) for i in range(1,9)],[[str(i)]+list(row) for i,row in enumerate(P8_MATRIX)], [0.13]+[0.87/8]*8)
para('<b>Proposition.</b> This matrix has exactly 36 complete EFX allocations. The numbers that also make agents 0, 1 and 2 ordinarily envy-free are, respectively, <b>0, 31 and 31</b>. It refutes P<sub>8</sub>. It has EFX allocations and therefore is not an EFX nonexistence counterexample.')
heading('A direct EFX witness',2)
eq(r'A_0=\{g_1,g_2,g_8\},\quad A_1=\{g_3,g_4,g_6\},\quad A_2=\{g_5,g_7\}.')
table(['Evaluating agent','Cost of A0','Cost of A1','Cost of A2','Own residual'],[['0',583,598,579,548],['1',312,331,858,307],['2',227,742,222,166]],[.24,.19,.19,.19,.19])
para('The own residuals 548, 307 and 166 are no greater than their corresponding other-bundle minima 579, 312 and 227. Agent 0 nevertheless envies agent 2, since 583 is greater than 579. This makes the distinction between EFX and the stronger prescribed-agent claim visible without a solver.')
heading('Exhaustive certificate',2)
para('The standard-library checker enumerates all 3<sup>8</sup> = 6,561 labelled allocations, including allocations with empty bundles. For each one it records an exact strict inequality: either agent 0\'s ordinary envy or an EFX violation. A separate certificate-replay routine reconstructs the allocation from its base-three identifier and recomputes both sides of the recorded inequality directly. Every one of the 6,561 rows passes; all arithmetic is integer arithmetic.')
para('Among the 36 EFX allocations, there are only ten possible bundles for agent 0. The following grouping gives their counts and the smallest ordinary-envy gap in each group. Every gap is positive. The group table supplements the exhaustive certificate; it is not used to assume that the list is exhaustive.')
from efx_exact import enumerate_efx
groups=collections.defaultdict(list)
for allocation in enumerate_efx(P8_MATRIX):
    bundles=[tuple(g+1 for g,i in enumerate(allocation) if i==k) for k in range(3)]
    val=[sum(P8_MATRIX[0][g-1] for g in b) for b in bundles]
    groups[bundles[0]].append(val[0]-min(val[1:]))
table(['Agent 0 bundle: chore numbers','EFX allocations','Smallest envy gap'],[['{'+', '.join(map(str,b))+'}',len(v),min(v)] for b,v in sorted(groups.items())],[.52,.23,.25],keep=True)
para('The displayed instance is strictly positive. It does not exploit the zero-cost convention, ties, floating-point tolerances or an incomplete allocation. Its counterexample property is stable under sufficiently small perturbations because there are finitely many strict failure witnesses.')

heading('5. Why appending one chore to this matrix cannot solve Problem 2')
para('Let the ninth chore have arbitrary nonnegative costs (x<sub>0</sub>, x<sub>1</sub>, x<sub>2</sub>). Three explicit allocations cover every possible added column. The bundle entries below are chore numbers, with 9 denoting the new chore.')
table(['Case','Agent 0','Agent 1','Agent 2','Sufficient condition'],[
 ['A','{5,6}','{1,2,3,4,8}','{7,9}','x2 <= 469'],
 ['B','{4,5}','{6,9}','{1,2,3,7,8}','x1 <= 494'],
 ['C','{9}','{1,3,6,8}','{2,4,5,7}','x1 >= 489 and x2 >= 457']], [.08,.15,.26,.26,.25])
para('In case A, agents 0 and 1 have residuals 304 and 469, while the relevant other-bundle minima are at least 332 and 500. Agent 2 has residual max(56,x<sub>2</sub>) and fixed comparison costs 666 and 469. In case B, agents 0 and 2 have residuals 247 and 286; their comparison minima are at least 304 and 401. Agent 1 has residual max(171,x<sub>1</sub>) and fixed comparison costs 494 and 836.')
para('In case C, agent 0 owns a singleton. Agents 1 and 2 have residuals 489 and 457; their costs for the other non-singleton bundle are 1,009 and 730. Their remaining comparisons are exactly the displayed lower bounds on x<sub>1</sub> and x<sub>2</sub>. If neither A nor B applies, then x<sub>2</sub> > 469 > 457 and x<sub>1</sub> > 494 > 489, so C applies. No restriction on x<sub>0</sub> is needed. This is a complete proof for this fixed eight-column family, including equality boundaries.')

page()
heading('6. Verification: what passed and what did not')
para('An external arithmetic proof check and an end-to-end formalisation are different levels of evidence. The successful checks below establish refutations of exact static SMT inputs. The interpretation of those inputs, the mathematical reductions, the soundness of the supplied proof calculus and the checker implementation remain explicit premises. No Lean, Rocq or Isabelle formalisation of the full fair-division argument is claimed.')
table(['Claim or search','Observed outcome','Scope'],[
 ['Ordinary seven-chore residual','cvc5 UNSAT; Ethos correct','Exact input-bound refutation. General coverage also uses the known six-chore theorem and minimum insertion.'],
 ['Prescribed-agent six chores','cvc5 UNSAT; Ethos correct','755-assertion input; zero rows handled mathematically.'],
 ['Ordinary eight-chore residual','Z3 UNSAT; native proof retained','The attempted external full-input run was killed without a verdict.'],
 ['Prescribed-agent seven-chore residual','Z3 UNSAT; '+('external core proof verified' if p7verified else 'external certificate not obtained'),'The full-input cvc5 attempt hit its imposed memory cap.'],
 ['Eight-chore displayed matrix','All 6,561 allocations checked','36 EFX allocations; no prescribed-agent-0 ordinary-EF witness.'],
 ['Nine chores with proved cuts','UNKNOWN after timeout','1,807.95 seconds; no mathematical verdict.'],
 ['Other nine-chore exact searches','No resolving verdict recorded','Some runs timed out; two broad root runs were killed under memory pressure.'],
], [.29,.28,.43])
heading('A material checker invocation error was corrected',2)
para('During verification, negative controls exposed that the pinned Ethos implementation resets its reference-state flag when the proof is opened as a positional file. An initial correct verdict in that mode checked a derivation without establishing the intended binding to the input assertions. Those receipts are retained with an explicit deprecated status and are not used as evidence of input-bound refutation.')
para('The corrected wrapper loads the reference and streams the proof through standard input. It removes only initial duplicate Real declarations that exactly match the reference constants, so the proof uses those same constants. Every proof definition, assumption and inference step is retained. The wrapper rejects commands that could reset input state, enforces a final proof of false at global assumption scope, and records both the original certificate hash and the actual streamed hash.')
para('Four controls passed: a valid refutation is accepted; deleting a required reference assertion causes rejection; a valid non-refuting prefix is accepted when a final contradiction is not required; the same prefix is rejected when that requirement is imposed. These controls test the binding and final-conclusion conditions. They do not prove the soundness of the checker itself.')
heading('Successful input-bound proof objects',2)
table(['Input','CPC inference steps','Raw CPC size','External checking time'],[
 ['Ordinary seven-chore residual','94,014','6,515,732 bytes','26.97 seconds'],
 ['Prescribed-agent six chores','857,855','70,716,103 bytes','90.49 seconds']], [.35,.21,.24,.20])
para('Both exports report zero trust/hole steps. The checked runs enable the core CPC signature, no expert signature and no rule-skipping option. Full SHA-256 hashes, source commits, exact commands and receipts are in the verification record. Timings describe these executions under their actual load; they are not promised runtimes.')
heading('Semantic audits and their limits',2)
para('For the prescribed-agent formulas, a separate parser audit compares all 2,535 saved allocation clauses with independently reconstructed exact integer coefficient vectors, and matches all 67 canonical-domain assertions. All agree. Seven exact fixtures per formula give 17,745 direct clause evaluations with zero disagreements; 762 additional checks cover omitted empty-bundle allocations on positive fixtures. These stronger syntax and coefficient checks still leave the handwritten equivalence argument distinct from the arithmetic proof checker.')
para('The main nine-chore allocation encoding was compared against an independently written literal predicate on 16 exact matrices and all 18,150 nonempty labelled allocations per matrix: 290,400 comparisons, with zero disagreements. A further rank-pruning audit made 236,196 comparisons over four representative ordering cases. These are bounded implementation checks; neither establishes that all real cost matrices admit EFX.')

heading('7. Remaining mathematical obligations')
para('The original target remains the satisfiability or refutability of the nine-chore nonexistence formula, with every mathematical reduction justified. No completed run produced a nine-chore counterexample, and no refutation covering the residual domain was obtained. The fixed-matrix extension proof in Section 5 excludes one proposed construction; it is not a universal extension theorem.')
para('One investigated conditional route asks whether P<sub>8</sub> holds when all three agents have distinct cheapest chores. The displayed obstruction does not answer that question because agents 0 and 1 share a minimum. If that conditional premise were proved, deleting an agent\'s minimum would show that every potential generic nine-chore counterexample has its second-cheapest chore among the other two pinned minima. There would then be two directed second-minimum patterns and seven remaining positions in agent 0\'s order: 14 canonical cones. The premise is unproved here. All 14 bounded cone checks returned UNKNOWN on their 45-second budgets, so they supply no completed cover.')
para('The accompanying proof record also gives small explicit counterexamples to two proposed marked-chore merge arguments. These prevent invalid shortcuts from entering a later draft. A solver-supported result for a stronger auxiliary property, or a failed construction of a counterexample, cannot fill the missing nine-chore inference.')
para('The continuation below adds a finite integer bound, a bounded real-arithmetic formulation, and two certificate-producing coverage searches. They strengthen the available methods without supplying the still-missing global refutation or exact nine-chore counterexample.')
heading('Release interpretation',2)
para('This package supports a research note on exact prescribed-agent obstructions, smaller-instance proof checking, and the remaining nine-chore gap. It does not support an announcement that Problem 2 has been solved. The literature search found no earlier prescribed-agent seven/eight boundary in its inspected corpus, but priority is bounded by that search, and a sharp boundary claim also requires its positive proof obligations. The novelty report records those distinctions.')

page()
heading('8. Reproduction and concrete sanity checks')
para('The fastest check uses only Python\'s standard library. From the extracted project directory:')
code('python src/verify_finite.py --out results/replay_finite.json')
para('The expected output is: 36 EFX allocations for the eight-chore matrix; prescribed ordinary-envy-free counts [0,31,31]; 1,680 EFX allocations for uniform positive nine-chore costs; and 19,683 EFX allocations when all costs are zero. It also produces and independently replays the 6,561-row failure certificate. No optimiser or network access is needed for this check.')
para('For independent arithmetic proof replay, use the pinned Ethos executable and the supplied CPC signatures. The archive contains the source pins, build notes, signatures and exact proof files; it omits a compiled checker. The source-build command requires the documented compiler/GMP prerequisites and network access. Its full build path was not rerun during packaging. The commands are:')
code('bash scripts/setup_checker.sh --build --jobs 2\n\npython src/check_ethos.py results/root7_pruned.smt2 \\\n  certificates/root7_cvc5.cpc \\\n  --checker work/checker_rebuilt/ethos/build/src/ethos \\\n  --report replay/root7_ethos.json\n\npython src/check_ethos.py \\\n  work/structural_designated_m6.standard.smt2 \\\n  certificates/designated6_cvc5.cpc \\\n  --checker work/checker_rebuilt/ethos/build/src/ethos \\\n  --report replay/designated6_ethos.json')
para('A successful replay must report result=verified, reference_binding=true, and requires_final_false_at_global_scope=true, with the documented standard-input adaptation. An incomplete verdict, missing proof, timeout or failed input binding is a failed replay. The archive README explains how to build the pinned checker on another machine and how to override checker/signature locations.')
heading('Sanity check 1: uniform nine-chore costs',2)
para('If every cost equals one, EFX says that the largest bundle size differs from the smallest by at most one. Since nine chores are divided among three agents, the only possible size pattern is (3,3,3). The exact number of labelled allocations is')
eq(r'\frac{9!}{(3!)^3}=1\,680.')
para('The independent checker returns precisely 1,680. With all costs zero, every one of the 19,683 complete allocations is EFX, including allocations with empty bundles.')
heading('Sanity check 2: the zero-removal convention',2)
para('Give every agent the same costs (0,1,1), and allocate the zero-cost chore and one unit chore to agent 0, the other unit chore to agent 1, and nothing to agent 2. Removing agent 0\'s zero-cost chore leaves cost 1, which exceeds the empty bundle\'s cost 0. The allocation therefore fails the required EFX definition. An erroneous checker that considers only positive-cost removals accepts it. Across all 27 allocations, the correct count is 6 and the weakened count is 18; the mutation control reproduces both.')

heading('9. Zero minima and complete finite representatives')
heading('A. Lower one cheapest chore per row to zero',2)
para('For each agent i, choose a globally cheapest chore e<sub>i</sub>. Replace only its cost c<sub>i</sub>(e<sub>i</sub>) by zero, leaving every other entry unchanged; call the new matrix D. For every owned bundle S, its worst deletion residual is unchanged. If e<sub>i</sub> is absent, none of its costs change. If it is present, both the bundle total and its minimum decrease by exactly c<sub>i</sub>(e<sub>i</sub>). This also handles a tied original minimum and a singleton bundle.')
eq(r'r_i^D(S)=r_i^C(S),\qquad D_i(T)\leq C_i(T).')
para('Consequently, if A is EFX for D, then for every i and j its original residual is at most its new comparison-bundle cost, which is at most the original comparison-bundle cost:')
eq(r'r_i^C(A_i)=r_i^D(A_i)\leq D_i(A_j)\leq C_i(A_j).')
para('<b>Thus every EFX allocation after zeroing was EFX beforehand.</b> In particular, every counterexample survives the operation. This changes a single coordinate of each row; it does not subtract the minimum from the entire row. Deletion of the owned zero-cost chore is essential to the residual identity.')
para('Start from a positive, rowwise-distinct counterexample as in Section 2, then zero its unique minima. Each row now has exactly one zero and all other entries remain positive and pairwise distinct. The existing shared-minimum reduction permits the nine-chore counterexample search to pin those zeros to three distinct chores. The zeroing lemma itself does not require distinct pins or the eight-chore theorem.')
heading('B. Only 21 free real variables',2)
para('After pinning c<sub>i</sub>(i)=0, independently scale each row to set one fixed positive reference entry to one. Reference columns (1,0,0) are all different from their own row\'s zero column, so this gives')
eq(r'c_i(i)=0,\qquad c_0(1)=c_1(0)=c_2(0)=1.')
para('Only 3(m-2) real entries remain free: 18 for eight chores and 21 for nine chores. Require all off-minimum entries positive, c<sub>0</sub>(1) &lt; c<sub>0</sub>(2), and the six free chore columns decreasing in row 0. Add the literal allocation-failure clauses. There is no cross-row total constraint, integer assumption or uniform margin in this strict real formulation.')
para('An empty-bundle allocation still fails automatically for m at least 4: some other bundle has at least two chores, and its owner has at most one zero-cost chore. A deletion therefore leaves a positive residual against the empty bundle. This proves the sufficiency of the 18,150 surjective allocation clauses. The independently audited serialized nine-chore input has 21 variables, 27 domain assertions and all 18,150 allocation clauses; it retains every required pinned-zero deletion.')
heading('C. A bounded integer representative',2)
para('<b>Theorem.</b> For three agents and m at least 4 chores, a counterexample has a representative with one zero in each row and all other entries positive integers at most')
eq(r'Z_m=\left\lfloor\sqrt{(m-2)(m-1)^{m-2}}\right\rfloor.')
para('The zero positions and the complete strict order of the positive costs may be preserved. The proof uses standard polyhedral, Cramer and Hadamard arguments [4]; no historical-priority claim is made for this specialization.')
para('<b>Proof.</b> From the zero-minimum counterexample, select a strict failed comparison for every allocation with three nonempty bundles. Assign it to its evaluating agent. Each such inequality uses only that row, so the rows may be replaced independently. Its coefficient vector has entries -1, 0 or 1 and support at most')
eq(r'|A_i|-1+|A_j|=m-|A_k|-1\leq m-2.')
para('Remove the fixed zero coordinate. There are d=m-1 variables in each row. Add positivity and the adjacent inequalities for its complete strict order; their support is at most two, hence at most m-2. The resulting finite homogeneous system A<sub>i</sub>x &gt; 0 is feasible. Scale a feasible row until all margins are at least one, giving a nonempty polyhedron P<sub>i</sub> = {x: A<sub>i</sub>x &gt;= 1}, with every coordinate at least one.')
para('Minimizing the sum of coordinates has a nonempty compact minimizing face: the sublevel set through any feasible point is closed and bounded because the coordinates are at least one. A vertex of that face is also a vertex of P<sub>i</sub>. At such a vertex v choose d independent active rows, obtaining a nonsingular integer matrix D with Dv = 1.')
para('Let D<sub>g</sub> replace column g by ones. Cramer\'s rule gives v<sub>g</sub> = det D<sub>g</sub> / det D. Every row of D has squared norm at most m-2; replacing one coefficient increases that norm by at most one. Because D is nonsingular, the replaced column has a nonzero entry in at least one row. In that row replacing -1 or 1 by 1 does not increase the squared norm. Hadamard\'s inequality therefore gives')
eq(r'|\det D_g|^2\leq(m-2)(m-1)^{d-1}=(m-2)(m-1)^{m-2}.')
para('Multiply v by the positive integer |det D|. Each resulting coordinate is an integer of magnitude |det D<sub>g</sub>|, positive and at most Z<sub>m</sub>. Every selected failure, positivity and order margin remains at least one. Restore the zero coordinate and repeat independently for all three rows. Each surjective allocation retains its selected failure; the empty-bundle argument handles every other allocation. This proves the theorem.')
eq(r'3831^2=14\,676\,561\leq7\cdot8^7=14\,680\,064<14\,684\,224=3832^2.')
para('Hence <b>Z<sub>9</sub> = 3,831</b>. There are 24 positive integer entries, with three pinned zeros. For eight chores, Z<sub>8</sub> = 840. The strict reference-normalized real search in part B is separate: its reference entries are one, whereas the integer representatives need not have reference value one.')
heading('D. Positive integer costs with common minimum one',2)
para('The zero representative also yields a strictly positive one with a controlled range. For each allocation select a strongest failed deletion comparison. Its integer margin is at least one. Raise each row\'s single zero entry to 1/2. Because every other cost is at least one, each worst owned residual remains unchanged; any target-bundle total rises by at most 1/2. Every selected failure therefore retains margin at least 1/2.')
para('Multiply all rows by two. Each row now has minimum exactly one; every other cost is an even integer between two and 2Z<sub>m</sub>, and every selected failure has margin at least one. For nine chores this proves the alternative complete representative range')
eq(r'c_i(e_i)=1,\qquad c_i(g)\in\{2,4,\ldots,7662\}\quad(g\ne e_i).')
para('<b>Interpretation.</b> Exhausting either complete range would settle the unrestricted nonnegative question, after the stated canonical reduction. Neither range has been exhausted here. These existence reductions may replace the original rows; they do not assert pointwise equivalence between an arbitrary original matrix and a bounded integer matrix.')
heading('Earlier finite bounds remain valid',2)
para('Before the zero-minimum reduction, separate nine-dimensional row systems gave a positive integer bound of 11,585, with independently valued minima. A projection refinement gives 10,822. An earlier 25-dimensional argument additionally forced equal integer minima and gave 194,368,031,998. All of those proofs remain in the archive. The sharper zero-based construction now gives both the smaller zero range 3,831 and the positive common-minimum range 7,662.')
para('The completed bounded real and prefix runs still used their original B = 11,585, with row-local margin 1/B. Their frozen inputs and receipts are unchanged. That older real normalization fixes minima to one and bounds entries by B; multiplying it by B gives real, not necessarily integer, variables. Its proof supplies no uniform margin for arbitrary cross-row total differences. The new zero-minimum run uses the strict reference-normalized formula in part B.')

heading('10. Exact certificates for sufficient families')
para('Both methods in this section turn a sampled case into a symbolic implication that holds throughout a stated region of valuation space. A verified region is a mathematical result for that family. A universal theorem additionally requires proving that the regions cover the entire required space.')
heading('A. Fix eight columns and vary the ninth',2)
para('Fix a three-by-eight prefix C and let x<sub>i</sub> be agent i\'s cost for the ninth chore. For any fixed complete allocation, every EFX comparison becomes q(C<sub>i</sub>) + s x<sub>i</sub> &lt;= 0, where s is -1, 0 or 1. Its feasible extension costs form a closed axis-aligned box, possibly empty or unbounded. All 19,683 allocations are represented by these boxes.')
para('Suppose a finite collection of boxes covers the required extension domain at a sampled prefix. An upper-bound failure x<sub>i</sub> &gt; U and a lower-bound failure x<sub>i</sub> &lt; L cannot both hold when U &gt;= L. A lower-bound failure alone is impossible when the recorded domain lower bound is at least L. These comparisons give homogeneous, row-local linear conditions on C.')
para('The certificate lists the exact EFX literals, the incompatibilities, and a finite exhaustive proof that failure of every selected allocation is impossible. Linear conditions removed during compression have exact nonnegative rational derivations from the retained conditions, nonnegative coordinates and explicitly recorded order assumptions. An independent standard-library checker reconstructs the literals, checks the identities and exhausts the Boolean alternatives.')
if continuation_status.get('prefix_evidence'):
    pe=continuation_status['prefix_evidence']
    para(f'The final bounded-prefix snapshot contains {pe["regions"]:,} independently checked regions: {pe["unrestricted_regions"]:,} cover every nonnegative ninth column, and {pe["restricted_regions"]:,} cover the recorded smaller domain. Its portable formula is bound to exactly 52 canonical assertions and those {pe["regions"]:,} region exclusions. The final search ended at its deadline without a global coverage verdict. Earlier frozen snapshots remain separately identified in the archive.')
else:
    para('The first frozen audited snapshot contains 641 such regions: 300 cover every nonnegative ninth column; 341 cover the recorded smaller domain. Its portable outer formula is bound to exactly 31 canonical assertions and those 641 region exclusions. That correspondence audit does not establish UNSAT. Later certificates and snapshots are included with their own stated scopes.')
heading('Why the smaller extension domain suffices',2)
para('Normalize each positive row minimum to one. Let F be the six chores other than the three distinct minima and T<sub>i</sub> its full row total. Choose i minimizing T<sub>i</sub> - max<sub>g in F</sub> c<sub>i</sub>(g), and delete a free chore e attaining that maximum. For every j,')
eq(r'T_j-c_j(e)\geq T_j-\max_{g\in F}c_j(g)\geq T_i-\max_{g\in F}c_i(g).')
para('The chosen row therefore has least prefix total and its deleted chore is at least as costly as every remaining free chore in that row. After relabelling it as row 0 and sorting the free prefix columns, the extension domain may be restricted to x<sub>0</sub> &gt;= c<sub>03</sub>, x<sub>1</sub> &gt;= c<sub>11</sub>, and x<sub>2</sub> &gt;= c<sub>22</sub>. The certificates record these restrictions explicitly.')
para('The earlier positive integer bound B = 11,585 justifies the completed bounded necessary-condition prefix search with row-local margins 1/B. Cross-row total comparisons remain merely strict. A small decrease in row 0\'s nonminimum full-row costs makes its prefix total uniquely least while preserving the finite strict witness margins. A SAT prefix remains only a candidate; a checked global UNSAT result would suffice. The full argument is in the continuation proof record.')
heading('B. Eliminate the first valuation row',2)
para('Use independent minimum normalization without cross-row total constraints. The first row ranges over its canonical order domain D<sub>0</sub>; the other rows range over D<sub>12</sub>. For a finite allocation list K, establish that no first-row valuation can make every allocation in K fail the first agent\'s EFX condition:')
eq(r'D_0\ \wedge\ \bigwedge_{A\in K}\operatorname{Bad}_0(A)\quad\mathrm{is\ unsatisfiable}.')
para('The corresponding region R<sub>K</sub> requires agents 1 and 2 to be EFX on every allocation in K. For any two rows in that region and any first row in D<sub>0</sub>, some allocation in K is good for agent 0, and that same allocation is already good for the other two agents. This proves full EFX throughout the region.')
para('Each first-row failure is a finite disjunction of strict linear inequalities. For every possible choice of one failure from each allocation in K, a certificate gives nonnegative rational weights, with positive total weight on strict inequalities, whose weighted coefficient sum is zero. Such strictly positive inequalities cannot sum to zero. The independent checker verifies every alternative using exact fractions and reconstructs every coefficient from the allocation.')
if continuation_status.get('row_evidence'):
    re=continuation_status['row_evidence']
    para(f'The final audited outer snapshot has {re["assertions"]:,} assertions: 18 domain assertions and {re["learned_exclusions"]:,} learned exclusions. It includes 3,238 ordinal singleton seeds and 1,048 static pair seeds, together with the retained certified cores and later learned regions. Each actual exclusion is bound to a locally checked guarantee. A global coverage refutation is still missing. Exact source counts and subset witnesses for removed redundant cores are recorded separately; overlapping historical files are not counted as additional regions.')
else:
    para('An audited frozen checkpoint contains 3,238 ordinal singleton regions, 1,048 pair regions and 501 distinct additional core regions. Its 4,805 assertions consist of 18 domain assertions and 4,787 learned exclusions. The additional cores contain 5,616 exhaustive branch records; the paired seeds add 4,192. Every learned clause in this snapshot has a locally checked guarantee. A global coverage refutation is still missing.')
heading('Broader regions from smaller allocation lists',2)
para('An implementation enumerated a table of 2,113,668 candidate robust allocation pairs. The refinement worker uses this table to select compatible pairs with few compressed premises, and checks a fresh exact certificate for every pair it actually uses. The entire table was not independently certified. If no suitable pair is available, an inner arithmetic search supplies a larger allocation list. Several archived fallback lists reduce to three or four allocations by exact deletion checks; the minimized certificates remain separate from unchanged earlier inputs. A later worker selects up to four distinct, undominated regions per model. No count of learned regions is interpreted as a percentage of the infinite valuation space.')
para('A checker defect found during adversarial review is recorded explicitly. An earlier core checker could accept floating coefficients that underflowed when combined with tiny rational weights. The repaired checker requires exact integer coefficients and exact rational weights; all legitimate retained certificates were replayed, and the adversarial fixture was rejected. The defect is not concealed by counting later successful checks.')

heading('11. What the continuation computations establish')
table(['Formulation or check','Observed result','Meaning'],[
 ['Uncoupled fixed-minimum eight chores','UNSAT in 21.58 seconds','Reproduces the known eight-chore residual; no new external proof object.'],
 ['Bounded real eight chores','UNSAT in 35.69 seconds','Validates the justified finite-bound formulation on the known case.'],
 ['Independent integer-row CP-SAT eight chores','UNKNOWN after 60 seconds','No SAT or UNSAT conclusion.'],
 ['Unsigned bit-vector eight chores','UNKNOWN: memory limit during preprocessing','Actual atoms and allocation clauses passed independent semantic checks; no refutation.'],
 ['Distinct-minimum prescribed-agent eight chores','UNKNOWN after 120 seconds','The additional prescribed-agent property remains unresolved.'],
], [.32,.29,.39])
if continuation_status.get('final_runs'):
    table(['Final continuation search','Outcome','Scope'],continuation_status['final_runs'],[.31,.28,.41])
para('Interrupted jobs without terminal receipts are recorded as interrupted without a mathematical verdict. A disappeared process is not labelled UNSAT, SAT, or a completed timeout. Later short runs use separate supervisors, durable heartbeats and enforced wall limits. Their authoritative receipts and frozen inputs are included.')
para('The independently checked finite bound and regional implications are complete within their stated scopes. Neither successful smaller-case reproduction nor any finite number of excluded regions proves universal nine-chore existence. A prospective release must keep the unresolved target explicit unless a full refutation or exact counterexample is added.')

heading('References and inspected sources')
para('[1] Zhang, X. (2026). <i>EFX allocations for three agents and seven or eight chores</i> (Version 2, 6 October 2026) [Preprint]. arXiv. <link href="https://arxiv.org/abs/2609.10585v2" color="#19656A">https://arxiv.org/abs/2609.10585v2</link>')
para('[2] Kobayashi, Y., Mahara, R., &amp; Sakamoto, S. (2025). <i>EFX allocations for indivisible chores: Matching-based approach</i>. Theoretical Computer Science, 1026, 115010. <link href="https://doi.org/10.1016/j.tcs.2024.115010" color="#19656A">https://doi.org/10.1016/j.tcs.2024.115010</link>. Inspected full preprint: <link href="https://arxiv.org/abs/2305.04168" color="#19656A">https://arxiv.org/abs/2305.04168</link>.')
para('[3] Yin, L., &amp; Mehta, R. (2022). <i>On the envy-free allocation of chores</i> [Preprint]. arXiv. <link href="https://arxiv.org/abs/2211.15836" color="#19656A">https://arxiv.org/abs/2211.15836</link>.')
para('[4] von zur Gathen, J., &amp; Sieveking, M. (1978). <i>A bound on solutions of linear integer equalities and inequalities</i>. Proceedings of the American Mathematical Society, 72(1), 155-158. <link href="https://doi.org/10.1090/S0002-9939-1978-0500555-0" color="#19656A">https://doi.org/10.1090/S0002-9939-1978-0500555-0</link>. The numerical representative bound here is derived self-containedly; this reference identifies the classical determinant method.')
para('Proof infrastructure: cvc5 1.4.1; Ethos commit 08e4aa40c4f8a6e00833f10e8d8985777e424027; cvc5 signature commit 2b2e84419f70817ec919a784a48806e79f677240. Primary implementation documentation: <link href="https://cvc5.github.io/docs/cvc5-1.4.1/proofs/output_cpc.html" color="#19656A">cvc5 1.4.1 CPC proof documentation</link>. Full provenance, licences and source links are retained in the archive.',small=True)
para('Inspection and novelty searches were conducted on 7 October 2026. The absence of a match in the recorded search is not a universal historical-priority determination. This memorandum makes no authorship or publication-status claim beyond the stated preparation purpose.',small=True)

def decorate(canvas, doc):
    canvas.saveState()
    canvas.setStrokeColor(LINE)
    canvas.setLineWidth(.5)
    if doc.page>1:
        canvas.line(MARGIN,H-34,W-MARGIN,H-34)
        canvas.setFont('Head',7.5)
        canvas.setFillColor(GREY)
        canvas.drawString(MARGIN,H-27,'NINE CHORES FOR THREE AGENTS')
        canvas.drawRightString(W-MARGIN,H-27,'RESEARCH MEMORANDUM | 7 OCTOBER 2026')
    canvas.line(MARGIN,35,W-MARGIN,35)
    canvas.setFont('Head',7.3)
    canvas.setFillColor(GREY)
    canvas.drawString(MARGIN,23,'Nine-chore target unresolved; ancillary scopes stated separately.')
    canvas.drawRightString(W-MARGIN,23,str(doc.page))
    canvas.restoreState()

doc=BaseDocTemplate(str(PDF),pagesize=A4,leftMargin=MARGIN,rightMargin=MARGIN,
                    topMargin=47,bottomMargin=47,title='Nine chores for three agents: research record',
                    author='Research preparation',subject='Unresolved nine-chore EFX target and exact ancillary results')
frame=Frame(MARGIN,47,WIDTH,H-94,leftPadding=0,rightPadding=0,topPadding=0,bottomPadding=0)
doc.addPageTemplates(PageTemplate(id='main',frames=[frame],onPage=decorate))
doc.build(story)
MD.write_text('\n'.join(markdown),encoding='utf-8')
print(json.dumps({'pdf':str(PDF),'markdown':str(MD),'p7_external_verified':p7verified,'bytes':PDF.stat().st_size}))
