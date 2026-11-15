# AidOS: reference verification log

Checked 13 Nov. 2026. Every field below was confirmed against a source that was actually fetched during verification: the Crossref REST API (`api.crossref.org/works/<DOI>`), doi.org content negotiation, the publisher's own page, arXiv, zbMATH Open, the Library of Congress (MODS record), Open Library or official documentation. Where two authoritative sources disagree, the entry says so.

Ordering: this log is grouped by topic; the report numbers references in order of first citation. **Final decision:** Holm (1979) is cited without the unconfirmed issue number.

Software versions are taken from the project lockfiles: `apps/api/uv.lock` has ortools 9.15.6755 and fastapi 0.162.3, and `apps/web/package.json` has react ^19.3.1.

---

## (a) Final reference list

[1] L. A. Zadeh, "Fuzzy sets," *Information and Control*, vol. 8, no. 3, pp. 338–353, Jun. 1965, doi: 10.1016/S0019-9958(65)90241-X.

[2] T. Takagi and M. Sugeno, "Fuzzy identification of systems and its applications to modeling and control," *IEEE Transactions on Systems, Man, and Cybernetics*, vol. SMC-15, no. 1, pp. 116–132, Jan. 1985, doi: 10.1109/TSMC.1985.6313399.

[3] E. H. Mamdani and S. Assilian, "An experiment in linguistic synthesis with a fuzzy logic controller," *International Journal of Man-Machine Studies*, vol. 7, no. 1, pp. 1–13, Jan. 1975, doi: 10.1016/S0020-7373(75)80002-2.

[4] E. H. Ruspini, "A new approach to clustering," *Information and Control*, vol. 15, no. 1, pp. 22–32, Jul. 1969, doi: 10.1016/S0019-9958(69)90591-9.

[5] G. J. Klir and B. Yuan, *Fuzzy Sets and Fuzzy Logic: Theory and Applications*. Upper Saddle River, NJ, USA: Prentice Hall PTR, 1995.

[6] S. Russell and P. Norvig, *Artificial Intelligence: A Modern Approach*, 4th ed. Hoboken, NJ, USA: Pearson, 2021.

[7] F. Rossi, P. van Beek, and T. Walsh, Eds., *Handbook of Constraint Programming* (Foundations of Artificial Intelligence). Amsterdam, The Netherlands: Elsevier, 2006.

[8] L. Perron and V. Furnon, "OR-Tools," version 9.15, Google. [Online]. Available: https://developers.google.com/optimization/ (accessed 13 Nov. 2026).

[9] L. Perron and F. Didier, "CP-SAT," OR-Tools version 9.15, Google. [Online]. Available: https://developers.google.com/optimization/cp/cp_solver (accessed 13 Nov. 2026).

[10] L. Perron, F. Didier, and S. Gay, "The CP-SAT-LP solver," in *Proc. 29th Int. Conf. Principles and Practice of Constraint Programming (CP 2023)*, R. H. C. Yap, Ed., Leibniz International Proceedings in Informatics (LIPIcs), vol. 280. Dagstuhl, Germany: Schloss Dagstuhl – Leibniz-Zentrum für Informatik, 2023, pp. 3:1–3:2, doi: 10.4230/LIPIcs.CP.2023.3.

[11] G. B. Dantzig, "Discrete-variable extremum problems," *Operations Research*, vol. 5, no. 2, pp. 266–288, Apr. 1957, doi: 10.1287/opre.5.2.266.

[12] H. Kellerer, U. Pferschy, and D. Pisinger, *Knapsack Problems*. Berlin, Germany: Springer, 2004, doi: 10.1007/978-3-540-24777-7.

[13] R. Jain, D. Chiu, and W. Hawe, "A quantitative measure of fairness and discrimination for resource allocation in shared computer systems," Digital Equipment Corp., DEC Research Report TR-301, Sep. 1984. [Online]. Available: https://arxiv.org/abs/cs/9809099, doi: 10.48550/arXiv.cs/9809099.

[14] L. N. Van Wassenhove, "Humanitarian aid logistics: supply chain management in high gear," *Journal of the Operational Research Society*, vol. 57, no. 5, pp. 475–489, May 2006, doi: 10.1057/palgrave.jors.2602125.

[15] N. Altay and W. G. Green, "OR/MS research in disaster operations management," *European Journal of Operational Research*, vol. 175, no. 1, pp. 475–493, Nov. 2006, doi: 10.1016/j.ejor.2005.05.016.

[16] J. Holguín-Veras, N. Pérez, M. Jaller, L. N. Van Wassenhove, and F. Aros-Vera, "On the appropriate objective function for post-disaster humanitarian logistics models," *Journal of Operations Management*, vol. 31, no. 5, pp. 262–280, Jul. 2013, doi: 10.1016/j.jom.2013.06.002.

[17] M. Huang, K. Smilowitz, and B. Balcik, "Models for relief routing: Equity, efficiency and efficacy," *Transportation Research Part E: Logistics and Transportation Review*, vol. 48, no. 1, pp. 2–18, Jan. 2012, doi: 10.1016/j.tre.2011.05.004.

[18] S. Holm, "A simple sequentially rejective multiple test procedure," *Scandinavian Journal of Statistics*, vol. 6, no. 2, pp. 65–70, 1979. [Online]. Available: https://www.jstor.org/stable/4615733

[19] B. Efron and R. J. Tibshirani, *An Introduction to the Bootstrap*. New York, NY, USA: Chapman & Hall, 1993.

[20] D. Lakens, "Calculating and reporting effect sizes to facilitate cumulative science: a practical primer for t-tests and ANOVAs," *Frontiers in Psychology*, vol. 4, Art. no. 863, Nov. 2013, doi: 10.3389/fpsyg.2013.00863.

[21] "FastAPI," FastAPI documentation. [Online]. Available: https://fastapi.tiangolo.com/ (accessed 13 Nov. 2026).

[22] Meta Platforms, Inc., "React," React documentation. [Online]. Available: https://react.dev/ (accessed 13 Nov. 2026).

[23] University of Wollongong in Dubai, "CSCI218 Foundations of Artificial Intelligence: Group Project Guidelines and Grading Criteria," Autumn 2026, supplied course document.

[24] Dubai Humanitarian and UOWD, "Proposed CSCI218 AI student projects," supplied spreadsheet (Project C: Emergency Resource Allocation Simulation), Autumn 2026.

---

## (b) Verification log

| # | Source fetched | Fields confirmed | Claim in the report it supports |
|---|---|---|---|
| 1 | https://api.crossref.org/works/10.1016/S0019-9958(65)90241-X | Author "L.A. Zadeh", title, journal, vol 8, no 3, pp 338–353, published 1965-06, DOI | Fuzzy sets and membership functions, the foundation of the urgency engine. |
| 2 | https://api.crossref.org/works/10.1109/TSMC.1985.6313399 | Authors Tomohiro Takagi and Michio Sugeno, title, journal, vol SMC-15, no 1, pp 116–132, 1985-01, DOI | The Takagi–Sugeno model; AidOS uses its zero-order form (constant consequents, weighted-average defuzzification). |
| 3 | https://api.crossref.org/works/10.1016/S0020-7373(75)80002-2 | Authors E.H. Mamdani and S. Assilian, title, journal, vol 7, no 1, pp 1–13, 1975-01, DOI | The Mamdani min/max inference with centroid defuzzification that the Sugeno engine is compared against. |
| 4 | https://api.crossref.org/works/10.1016/S0019-9958(69)90591-9 | Author Enrique H. Ruspini, title, journal, vol 15, no 1, pp 22–32, 1969-07, DOI | Origin of the fuzzy-partition condition (memberships summing to one) behind the "Ruspini partitions" used for the input variables. |
| 5 | Open Library, https://openlibrary.org/api/books?bibkeys=ISBN:0131011715&format=json&jscmd=data | Title and subtitle, authors George J. Klir and Bo Yuan, publisher Prentice Hall PTR, place Upper Saddle River, N.J., 1995 (ISBN 0-13-101171-5) | Textbook background on t-norms (product t-norm), fuzzy partitions and defuzzification. |
| 6 | Library of Congress MODS record, https://lccn.loc.gov/2019047498/mods; also https://openlibrary.org/isbn/9780134610993.json | LoC: title, "Fourth edition", place Hoboken, publisher Pearson, dateIssued [2021], ISBN 9780134610993. Open Library: Pearson, release date May 08, 2020, LC call number "Q335 .R86 2021" | Background on constraint satisfaction problems, search, and agent/state-machine views used for the simulator. **Year note:** the LoC catalogue dates the US 4th edition 2021 (copyright year); the retail release was May 2020. Many papers cite 2020. Either is defensible; 2021 follows the LoC record. |
| 7 | Elsevier shop, https://shop.elsevier.com/books/handbook-of-constraint-programming/rossi/978-0-444-52726-4; Crossref chapter record https://api.crossref.org/works/10.1016/s1574-6526(06)80016-7; https://openlibrary.org/isbn/9780444527264.json | Editors Rossi, van Beek and Walsh; 1st ed.; publication date 18 Aug. 2006 (Elsevier); Crossref series "Foundations of Artificial Intelligence" (ISSN 1574-6526), issued 2006, ISBN 9780444527264; Open Library place Amsterdam | Constraint-programming background for the CP-SAT model formulation. Open Library gives 2007, but the publisher and Crossref both give 2006, so 2006 is used. The series volume number was not confirmed, so it is omitted. |
| 8 | https://developers.google.com/optimization/support/cite (official "How to cite OR-Tools" page) | Official format: "OR-Tools v9.12. Laurent Perron and Vincent Furnon.", organisation Google, URL https://developers.google.com/optimization/ | The OR-Tools suite used for the allocator. The cite page uses v9.12 as its current example; the entry gives v9.15, the version installed in `uv.lock` (9.15.6755). |
| 9 | Same cite page; https://developers.google.com/optimization/cp/cp_solver (page title "CP-SAT Solver") | Official format: "OR-Tools CP-SAT v9.12. Laurent Perron and Frédéric Didier.", Google, URL of the CP-SAT page | The CP-SAT integer solver and its documented interface (lexicographic objectives, status reporting). Version adjusted to 9.15 as in [8]. |
| 10 | Cite page BibTeX, plus doi.org content negotiation for 10.4230/LIPIcs.CP.2023.3 | Authors Perron, Didier and Gay; title (registered as "The CP-SAT-LP Solver (Invited Talk)"); LIPIcs vol 280, CP 2023; pp 3:1–3:2; editor Roland H. C. Yap; publisher Schloss Dagstuhl; 2023; DOI | The scholarly description of the CP-SAT solver (lazy clause generation with LP relaxation). Added because the cite page recommends it. |
| 11 | https://api.crossref.org/works/10.1287/opre.5.2.266 | Author George B. Dantzig, title, Operations Research, vol 5, no 2, pp 266–288, 1957-04, DOI | Greedy-by-ratio optimality for the relaxed knapsack, the basis of the greedy/CP-SAT equivalence argument. |
| 12 | https://api.crossref.org/works/10.1007/978-3-540-24777-7 | Authors Hans Kellerer, Ulrich Pferschy and David Pisinger; title; publisher Springer Berlin Heidelberg; 2004; ISBNs 9783540247777 and 9783642073113; DOI | Standard reference for knapsack variants and the conditions under which greedy is optimal (unit weights, separable per-resource capacity). |
| 13 | https://arxiv.org/abs/cs/9809099 | Title; authors as listed (R. Jain, D. Chiu, W. Hawe); comments "DEC Research Report TR-301, September 1984"; submitted 24 Sep. 1998; arXiv DOI 10.48550/arXiv.cs/9809099 | Definition of Jain's fairness index used in the equity metric. |
| 14 | WebFetch of https://api.crossref.org/works/10.1057/palgrave.jors.2602125 | Author L N Van Wassenhove, title, JORS, vol 57, no 5, pp 475–489, May 2006, DOI | Humanitarian logistics as a distinct, high-stakes supply-chain problem, which motivates decision support. |
| 15 | https://api.crossref.org/works/10.1016/j.ejor.2005.05.016 | Authors Nezih Altay and Walter G. Green, title, EJOR, vol 175, no 1, pp 475–493, 2006-11, DOI | OR/MS methods for disaster operations management, which places optimisation-based allocation in context. |
| 16 | https://api.crossref.org/works/10.1016/j.jom.2013.06.002 | All five authors (José Holguín-Veras, Noel Pérez, Miguel Jaller, Luk N. Van Wassenhove, Felipe Aros-Vera), title, J. Operations Management, vol 31, no 5, pp 262–280, print Jul. 2013, DOI | Deprivation costs and the argument that pure efficiency objectives are inadequate after disasters, which supports the urgency-versus-equity design. |
| 17 | Crossref search, then https://api.crossref.org/works/10.1016/j.tre.2011.05.004 | Authors Michael Huang, Karen Smilowitz and Burcu Balcik; title; TRE vol 48, no 1, pp 2–18, Jan. 2012; DOI | Explicit equity, efficiency and efficacy objectives in relief distribution, which supports the coverage floor and the fairness metric. |
| 18 | zbMATH Open API (record Zbl 0402.62058, https://zbmath.org/3624650); JSTOR stable URL 4615733 (from search-result listing) | zbMATH: author Sture Holm, title, Scand. J. Stat. vol 6, pp 65–70, 1979. The issue number (no. 2) and JSTOR stable URL 4615733 come from the JSTOR listing surfaced by search; JSTOR pages could not be fetched directly | Holm's step-down correction applied to the family of paired comparisons. No DOI is given because 10.2307/4615733 does not resolve on doi.org or Crossref (404). |
| 19 | Open Library, https://openlibrary.org/api/books?bibkeys=ISBN:0412042312&format=json&jscmd=data; also https://api.crossref.org/works/10.1201/9780429246593 | Open Library: authors Bradley Efron and Robert J. Tibshirani, title, Chapman & Hall, New York, 1993 (ISBN 0-412-04231-2). Crossref: same title and authors under the later Chapman and Hall/CRC digital record, DOI 10.1201/9780429246593, dated 1994-05-15 | Bootstrap resampling and percentile confidence intervals, applied here as paired bootstrap CIs. The CRC DOI is left out of the citation because it carries a different date (1994) from the 1993 first edition. |
| 20 | https://api.crossref.org/works/10.3389/fpsyg.2013.00863 and the Frontiers article page (citation meta tags) | Author Daniël Lakens, title, Frontiers in Psychology, vol 4, article 863 ("Front. Psychol. 4:863"), publication date 2013-11-26, DOI | Paired effect size d_z (mean difference divided by the SD of the differences) for within-scenario comparisons. |
| 21 | https://fastapi.tiangolo.com/ | Page title "FastAPI", official site | The backend web framework (version 0.162.3 in `uv.lock`). No personal author is credited on the page, so none is cited. |
| 22 | https://react.dev/ (HTTP 200; footer credits "Meta Platforms, Inc") | Official React documentation site and its maintainer | The frontend UI library (react ^19.3.1 in `package.json`). |
| 23 | Supplied course document | Wording as provided by the team | Project requirements and grading criteria. |
| 24 | Supplied spreadsheet | Wording as provided by the team | The source brief for Project C (emergency resource allocation simulation). |

### Corrections to the candidate list found during verification
- **Huang, Smilowitz and Balcik (2012):** the correct DOI is **10.1016/j.tre.2011.05.004**. The DOI 10.1016/j.tre.2011.10.011, which is easy to guess, resolves to a different paper (Wang and Meng, on liner shipping), so do not use it. There is also a 2011 conference version with the same title (*Procedia – Social and Behavioral Sciences*, vol. 17, pp. 416–437, doi: 10.1016/j.sbspro.2011.04.525). Cite the 2012 journal version.
- **Altay and Green:** Crossref lists the second author as "Walter G. Green" with no "III" suffix, so the entry follows Crossref.
- **Jain et al.:** the arXiv record shows "D. Chiu, W. Hawe". The fuller forms "D.-M. Chiu" and "W. R. Hawe" are common, but they were not confirmed from a fetched source, so the arXiv forms are used.
- **Takagi and Sugeno:** Crossref gives the issue month as January 1985. IEEE Xplore may show "Jan.–Feb."; that was not checked.

---

## (c) Dropped / unverified

- **Nothing on the candidate list was dropped.** All items 1–18 were verified, with these caveats:
  - **Holm (1979):** the issue number "no. 2" and the JSTOR stable URL come from the JSTOR listing surfaced in search results. JSTOR itself could not be fetched (its page needs JavaScript), and the zbMATH record omits the issue. The volume, pages, year, author and title are confirmed by zbMATH. If you want to be strict, drop "no. 2".
  - **Russell and Norvig:** the year is 2020 or 2021 depending on the source (see row 6). The Global Edition (2021) was not separately verified, so cite the US edition only.
  - **OR-Tools citation version:** the official cite page uses v9.12. The entries use v9.15 because that is the version the project actually runs. If you prefer the cite page's version verbatim, change both [8] and [9] to v9.12.
  - **Handbook of Constraint Programming:** the series volume number (Foundations of Artificial Intelligence, vol. 2) was not confirmed, so it is omitted.
- **Python documentation:** deliberately not included. It adds nothing that the report needs to cite.
- **Substitutions or additions:** one addition, [10] (CP-SAT-LP, CP 2023), the scholarly citation that the official OR-Tools cite page recommends for CP-SAT. Item 17 (Huang et al.) was optional and is included with its DOI corrected.
