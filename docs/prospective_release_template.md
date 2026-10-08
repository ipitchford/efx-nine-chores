**Draft for Evidence Press editorial consideration**

**Nine chores can always be divided among three people with a strong fairness guarantee**

A computer-assisted proof establishes that any nine indivisible chores can be divided among three people so that removing any one chore from a person's own assignment leaves that person with no more burden than they assign to anyone else's bundle.

The guarantee is known as envy-freeness up to any chore, or EFX. It allows people to disagree about how burdensome each chore is. The assumption is that a person's costs add across chores. Costs may be zero, and the guarantee still applies when the removed chore is one that costs its owner nothing.

The proof covers the full range of nonnegative costs. It first shows that any counterexample would have a normalized representative described by 21 real variables. It then expresses failure of every relevant allocation as an exact system of logical and linear conditions. There are 19,683 complete ways to assign the nine chores; 18,150 appear directly in the formula, while a separate argument covers all 1,533 assignments with an empty bundle.

A solver found that these counterexample conditions are inconsistent. A separate checking program validates the resulting proof using exact rational arithmetic and elementary Boolean deductions. The certificate's arithmetic identities rule out contradictory collections of inequalities, and its logical steps combine them into a refutation of the complete counterexample formula. The checking program does not rely on the solver's reported answer.

The accompanying research package contains the written proof, the computational certificate, its verification programs, and an exact allocation finder. For any rational input matrix, the finder returns an allocation together with all the inequalities needed to check its fairness directly.

The inspected prior work establishes the seven- and eight-chore cases. This result resolves the nine-chore question posed as Problem 2 in the supplied economics shortlist. Its scope is three people, nine chores, and additive costs; it makes no claim about arbitrary numbers of chores or other models of preferences.

The manuscript and reproducibility package are prepared for editorial and mathematical review. No external publication or peer-review endorsement is asserted.
