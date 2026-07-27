# Stage-A 210 道 k5 失败题详情

Stage-A 定义：假设已经知道 k5 在哪 210 题失败，并用 ORM v2 band 规则（δ=0.1，池为 merged4 n4）替换。
此表仅用于分析选择器上限，不可部署。

| qid | db_id | k5 结果 | 是否 k5 空/报错 | 替换后是否修复 | 选中模型 | 选中 score | 备注 |
|---|---|---|---|---|---|---|---|
| 21 | california_schools | non-empty | False | False | omnisql | 0.6792 | 非空/非报错，ORM 未选对 |
| 24 | california_schools | non-empty | False | False | agentar | 0.6514 | 非空/非报错，ORM 未选对 |
| 27 | california_schools | non-empty | False | False | omnisql | 0.3208 | 非空/非报错，ORM 未选对 |
| 36 | california_schools | non-empty | False | False | agentar | 0.8355 | 非空/非报错，ORM 未选对 |
| 49 | california_schools | non-empty | False | False | agentar | 0.4073 | 非空/非报错，ORM 未选对 |
| 70 | california_schools | non-empty | False | False | agentar | 0.6514 | 非空/非报错，ORM 未选对 |
| 77 | california_schools | non-empty | False | True | agentar | 0.7773 | Stage-A 可修复但触发器未触发（非空/非报错） |
| 82 | california_schools | non-empty | False | False | qwen3 | 0.8808 | 非空/非报错，ORM 未选对 |
| 84 | california_schools | non-empty | False | False | omnisql | 0.3208 | 非空/非报错，ORM 未选对 |
| 86 | california_schools | empty | True | False | omnisql | 0.1480 | 触发但 ORM 选择仍错 |
| 94 | financial | non-empty | False | True | agentar | 0.2227 | Stage-A 可修复但触发器未触发（非空/非报错） |
| 99 | financial | non-empty | False | False | agentar | 0.4688 | 非空/非报错，ORM 未选对 |
| 100 | financial | non-empty | False | True | omnisql-921 | 0.4688 | Stage-A 可修复但触发器未触发（非空/非报错） |
| 106 | financial | non-empty | False | False | omnisql-921 | 0.5927 | 非空/非报错，ORM 未选对 |
| 113 | financial | non-empty | False | False | agentar | 0.7982 | 非空/非报错，ORM 未选对 |
| 122 | financial | error | True | True | omnisql | 0.9526 | Stage-A 修复且最终触发也修复 |
| 129 | financial | non-empty | False | False | agentar | 0.2018 | 非空/非报错，ORM 未选对 |
| 132 | financial | non-empty | False | False | omnisql | 0.7982 | 非空/非报错，ORM 未选对 |
| 133 | financial | non-empty | False | False | agentar | 0.5622 | 非空/非报错，ORM 未选对 |
| 142 | financial | non-empty | False | False | agentar | 0.9047 | 非空/非报错，ORM 未选对 |
| 143 | financial | empty | True | False | omnisql-921 | 0.2942 | 触发但 ORM 选择仍错 |
| 162 | financial | non-empty | False | False | agentar | 0.9740 | 非空/非报错，ORM 未选对 |
| 172 | financial | non-empty | False | False | omnisql | 0.7311 | 非空/非报错，ORM 未选对 |
| 179 | financial | non-empty | False | False | agentar | 0.7982 | 非空/非报错，ORM 未选对 |
| 181 | financial | non-empty | False | False | agentar | 0.5622 | 非空/非报错，ORM 未选对 |
| 182 | financial | non-empty | False | False | omnisql-921 | 0.6225 | 非空/非报错，ORM 未选对 |
| 185 | financial | non-empty | False | True | qwen3 | 0.6792 | Stage-A 可修复但触发器未触发（非空/非报错） |
| 192 | financial | non-empty | False | False | agentar | 0.7058 | 非空/非报错，ORM 未选对 |
| 205 | toxicology | non-empty | False | False | omnisql | 0.9241 | 非空/非报错，ORM 未选对 |
| 207 | toxicology | non-empty | False | False | agentar | 0.7058 | 非空/非报错，ORM 未选对 |
| 212 | toxicology | non-empty | False | False | agentar | 0.8355 | 非空/非报错，ORM 未选对 |
| 214 | toxicology | non-empty | False | True | agentar | 0.5000 | Stage-A 可修复但触发器未触发（非空/非报错） |
| 215 | toxicology | non-empty | False | False | agentar | 0.5622 | 非空/非报错，ORM 未选对 |
| 218 | toxicology | non-empty | False | False | agentar | 0.3775 | 非空/非报错，ORM 未选对 |
| 231 | toxicology | empty | True | False | agentar | 0.2227 | 触发但 ORM 选择仍错 |
| 234 | toxicology | non-empty | False | False | omnisql-921 | 0.8176 | 非空/非报错，ORM 未选对 |
| 252 | toxicology | non-empty | False | False | qwen3 | 0.6514 | 非空/非报错，ORM 未选对 |
| 269 | toxicology | non-empty | False | False | agentar | 0.6514 | 非空/非报错，ORM 未选对 |
| 281 | toxicology | non-empty | False | False | qwen3 | 0.7549 | 非空/非报错，ORM 未选对 |
| 286 | toxicology | non-empty | False | True | agentar | 0.2689 | Stage-A 可修复但触发器未触发（非空/非报错） |
| 288 | toxicology | non-empty | False | True | omnisql | 0.9669 | Stage-A 可修复但触发器未触发（非空/非报错） |
| 290 | toxicology | non-empty | False | True | omnisql | 0.7058 | Stage-A 可修复但触发器未触发（非空/非报错） |
| 296 | toxicology | non-empty | False | False | omnisql | 0.8670 | 非空/非报错，ORM 未选对 |
| 310 | toxicology | non-empty | False | False | agentar | 0.7773 | 非空/非报错，ORM 未选对 |
| 340 | card_games | empty | True | False | omnisql | 0.2689 | 触发但 ORM 选择仍错 |
| 341 | card_games | non-empty | False | False | agentar | 0.4378 | 非空/非报错，ORM 未选对 |
| 342 | card_games | non-empty | False | False | agentar | 0.4688 | 非空/非报错，ORM 未选对 |
| 343 | card_games | non-empty | False | False | omnisql | 0.8355 | 非空/非报错，ORM 未选对 |
| 349 | card_games | non-empty | False | False | agentar | 0.8355 | 非空/非报错，ORM 未选对 |
| 359 | card_games | non-empty | False | False | omnisql | 0.8176 | 非空/非报错，ORM 未选对 |
| 360 | card_games | non-empty | False | False | omnisql | 0.7549 | 非空/非报错，ORM 未选对 |
| 376 | card_games | non-empty | False | False | omnisql | 0.8355 | 非空/非报错，ORM 未选对 |
| 386 | card_games | non-empty | False | False | qwen3 | 0.6514 | 非空/非报错，ORM 未选对 |
| 387 | card_games | non-empty | False | False | agentar | 0.6792 | 非空/非报错，ORM 未选对 |
| 388 | card_games | non-empty | False | False | agentar | 0.7058 | 非空/非报错，ORM 未选对 |
| 389 | card_games | non-empty | False | False | agentar | 0.7773 | 非空/非报错，ORM 未选对 |
| 395 | card_games | non-empty | False | False | omnisql-921 | 0.8355 | 非空/非报错，ORM 未选对 |
| 400 | card_games | non-empty | False | True | agentar | 0.7311 | Stage-A 可修复但触发器未触发（非空/非报错） |
| 405 | card_games | non-empty | False | True | agentar | 0.8808 | Stage-A 可修复但触发器未触发（非空/非报错） |
| 406 | card_games | non-empty | False | False | omnisql-921 | 0.5312 | 非空/非报错，ORM 未选对 |
| 408 | card_games | non-empty | False | False | omnisql | 0.6225 | 非空/非报错，ORM 未选对 |
| 428 | card_games | empty | True | False | omnisql | 0.2018 | 触发但 ORM 选择仍错 |
| 432 | card_games | non-empty | False | False | agentar | 0.7773 | 非空/非报错，ORM 未选对 |
| 441 | card_games | non-empty | False | False | agentar | 0.8355 | 非空/非报错，ORM 未选对 |
| 444 | card_games | non-empty | False | False | qwen3 | 0.8933 | 非空/非报错，ORM 未选对 |
| 445 | card_games | non-empty | False | False | qwen3 | 0.7549 | 非空/非报错，ORM 未选对 |
| 448 | card_games | non-empty | False | False | omnisql-921 | 0.8808 | 非空/非报错，ORM 未选对 |
| 453 | card_games | non-empty | False | True | agentar | 0.9149 | Stage-A 可修复但触发器未触发（非空/非报错） |
| 454 | card_games | non-empty | False | False | omnisql | 0.8670 | 非空/非报错，ORM 未选对 |
| 482 | card_games | non-empty | False | False | agentar | 0.8355 | 非空/非报错，ORM 未选对 |
| 483 | card_games | non-empty | False | True | agentar | 0.7982 | Stage-A 可修复但触发器未触发（非空/非报错） |
| 484 | card_games | non-empty | False | False | agentar | 0.7982 | 非空/非报错，ORM 未选对 |
| 487 | card_games | non-empty | False | False | omnisql-921 | 0.4073 | 非空/非报错，ORM 未选对 |
| 500 | card_games | non-empty | False | False | omnisql | 0.5000 | 非空/非报错，ORM 未选对 |
| 515 | card_games | empty | True | False | omnisql-921 | 0.3208 | 触发但 ORM 选择仍错 |
| 516 | card_games | non-empty | False | True | agentar | 0.8520 | Stage-A 可修复但触发器未触发（非空/非报错） |
| 517 | card_games | non-empty | False | True | agentar | 0.7549 | Stage-A 可修复但触发器未触发（非空/非报错） |
| 519 | card_games | empty | True | False | omnisql | 0.1645 | 触发但 ORM 选择仍错 |
| 529 | card_games | empty | True | False | qwen3 | 0.3208 | 触发但 ORM 选择仍错 |
| 556 | codebase_community | non-empty | False | True | agentar | 0.4073 | Stage-A 可修复但触发器未触发（非空/非报错） |
| 581 | codebase_community | non-empty | False | False | agentar | 0.8176 | 非空/非报错，ORM 未选对 |
| 582 | codebase_community | non-empty | False | False | omnisql | 0.9149 | 非空/非报错，ORM 未选对 |
| 583 | codebase_community | non-empty | False | False | agentar | 0.7549 | 非空/非报错，ORM 未选对 |
| 586 | codebase_community | non-empty | False | False | omnisql | 0.8670 | 非空/非报错，ORM 未选对 |
| 587 | codebase_community | non-empty | False | False | omnisql | 0.2018 | 非空/非报错，ORM 未选对 |
| 593 | codebase_community | non-empty | False | True | omnisql-921 | 0.8355 | Stage-A 可修复但触发器未触发（非空/非报错） |
| 594 | codebase_community | non-empty | False | False | omnisql | 0.9399 | 非空/非报错，ORM 未选对 |
| 596 | codebase_community | non-empty | False | False | agentar | 0.3208 | 非空/非报错，ORM 未选对 |
| 602 | codebase_community | non-empty | False | False | agentar | 0.8520 | 非空/非报错，ORM 未选对 |
| 606 | codebase_community | empty | True | True | omnisql | 0.8670 | Stage-A 修复且最终触发也修复 |
| 608 | codebase_community | non-empty | False | True | omnisql | 0.9241 | Stage-A 可修复但触发器未触发（非空/非报错） |
| 628 | codebase_community | non-empty | False | False | agentar | 0.7058 | 非空/非报错，ORM 未选对 |
| 630 | codebase_community | empty | True | False | agentar | 0.1824 | 触发但 ORM 选择仍错 |
| 631 | codebase_community | non-empty | False | False | omnisql-921 | 0.9325 | 非空/非报错，ORM 未选对 |
| 632 | codebase_community | non-empty | False | False | agentar | 0.9325 | 非空/非报错，ORM 未选对 |
| 639 | codebase_community | non-empty | False | False | qwen3 | 0.2227 | 非空/非报错，ORM 未选对 |
| 640 | codebase_community | non-empty | False | False | agentar | 0.8176 | 非空/非报错，ORM 未选对 |
| 642 | codebase_community | non-empty | False | False | agentar | 0.5312 | 非空/非报错，ORM 未选对 |
| 646 | codebase_community | non-empty | False | False | omnisql | 0.7773 | 非空/非报错，ORM 未选对 |
| 649 | codebase_community | non-empty | False | False | agentar | 0.6514 | 非空/非报错，ORM 未选对 |
| 679 | codebase_community | non-empty | False | False | agentar | 0.9149 | 非空/非报错，ORM 未选对 |
| 682 | codebase_community | non-empty | False | False | agentar | 0.2018 | 非空/非报错，ORM 未选对 |
| 686 | codebase_community | non-empty | False | False | agentar | 0.9047 | 非空/非报错，ORM 未选对 |
| 687 | codebase_community | non-empty | False | False | omnisql | 0.8355 | 非空/非报错，ORM 未选对 |
| 694 | codebase_community | non-empty | False | False | agentar | 0.7058 | 非空/非报错，ORM 未选对 |
| 701 | codebase_community | non-empty | False | False | agentar | 0.3208 | 非空/非报错，ORM 未选对 |
| 706 | codebase_community | empty | True | False | agentar | 0.2451 | 触发但 ORM 选择仍错 |
| 709 | codebase_community | non-empty | False | False | agentar | 0.8176 | 非空/非报错，ORM 未选对 |
| 710 | codebase_community | non-empty | False | False | omnisql | 0.7773 | 非空/非报错，ORM 未选对 |
| 715 | codebase_community | non-empty | False | True | omnisql-921 | 0.8933 | Stage-A 可修复但触发器未触发（非空/非报错） |
| 720 | superhero | non-empty | False | False | agentar | 0.5622 | 非空/非报错，ORM 未选对 |
| 766 | superhero | empty | True | True | omnisql | 0.9526 | Stage-A 修复且最终触发也修复 |
| 805 | superhero | non-empty | False | False | omnisql | 0.7773 | 非空/非报错，ORM 未选对 |
| 811 | superhero | non-empty | False | False | omnisql | 0.9047 | 非空/非报错，ORM 未选对 |
| 812 | superhero | non-empty | False | False | agentar | 0.6792 | 非空/非报错，ORM 未选对 |
| 828 | superhero | non-empty | False | False | omnisql | 0.8520 | 非空/非报错，ORM 未选对 |
| 837 | superhero | non-empty | False | False | agentar | 0.9399 | 非空/非报错，ORM 未选对 |
| 847 | formula_1 | non-empty | False | False | agentar | 0.9466 | 非空/非报错，ORM 未选对 |
| 849 | formula_1 | non-empty | False | False | agentar | 0.9526 | 非空/非报错，ORM 未选对 |
| 851 | formula_1 | empty | True | True | qwen3 | 0.4378 | Stage-A 修复且最终触发也修复 |
| 855 | formula_1 | non-empty | False | False | omnisql-921 | 0.9466 | 非空/非报错，ORM 未选对 |
| 857 | formula_1 | non-empty | False | False | agentar | 0.9526 | 非空/非报错，ORM 未选对 |
| 866 | formula_1 | non-empty | False | False | agentar | 0.3775 | 非空/非报错，ORM 未选对 |
| 888 | formula_1 | non-empty | False | False | agentar | 0.9325 | 非空/非报错，ORM 未选对 |
| 889 | formula_1 | non-empty | False | False | agentar | 0.9579 | 非空/非报错，ORM 未选对 |
| 891 | formula_1 | non-empty | False | False | agentar | 0.7773 | 非空/非报错，ORM 未选对 |
| 894 | formula_1 | non-empty | False | False | agentar | 0.7058 | 非空/非报错，ORM 未选对 |
| 895 | formula_1 | non-empty | False | False | agentar | 0.9149 | 非空/非报错，ORM 未选对 |
| 897 | formula_1 | non-empty | False | False | agentar | 0.4378 | 非空/非报错，ORM 未选对 |
| 898 | formula_1 | non-empty | False | False | agentar | 0.9047 | 非空/非报错，ORM 未选对 |
| 908 | formula_1 | non-empty | False | False | agentar | 0.8176 | 非空/非报错，ORM 未选对 |
| 915 | formula_1 | non-empty | False | False | agentar | 0.9325 | 非空/非报错，ORM 未选对 |
| 922 | formula_1 | non-empty | False | False | agentar | 0.9325 | 非空/非报错，ORM 未选对 |
| 928 | formula_1 | non-empty | False | False | agentar | 0.9526 | 非空/非报错，ORM 未选对 |
| 937 | formula_1 | non-empty | False | False | omnisql-921 | 0.9241 | 非空/非报错，ORM 未选对 |
| 943 | formula_1 | non-empty | False | False | agentar | 0.5927 | 非空/非报错，ORM 未选对 |
| 958 | formula_1 | non-empty | False | False | agentar | 0.8355 | 非空/非报错，ORM 未选对 |
| 959 | formula_1 | empty | True | False | agentar | 0.8808 | 触发但 ORM 选择仍错 |
| 970 | formula_1 | non-empty | False | False | omnisql-921 | 0.6225 | 非空/非报错，ORM 未选对 |
| 986 | formula_1 | non-empty | False | False | agentar | 0.7982 | 非空/非报错，ORM 未选对 |
| 987 | formula_1 | non-empty | False | False | agentar | 0.5927 | 非空/非报错，ORM 未选对 |
| 989 | formula_1 | non-empty | False | False | agentar | 0.9047 | 非空/非报错，ORM 未选对 |
| 990 | formula_1 | empty | True | True | qwen3 | 0.8933 | Stage-A 修复且最终触发也修复 |
| 993 | formula_1 | non-empty | False | False | agentar | 0.9669 | 非空/非报错，ORM 未选对 |
| 998 | formula_1 | empty | True | False | agentar | 0.4688 | 触发但 ORM 选择仍错 |
| 1000 | formula_1 | non-empty | False | False | agentar | 0.9466 | 非空/非报错，ORM 未选对 |
| 1004 | formula_1 | non-empty | False | False | omnisql | 0.5927 | 非空/非报错，ORM 未选对 |
| 1006 | formula_1 | non-empty | False | False | omnisql | 0.7982 | 非空/非报错，ORM 未选对 |
| 1009 | formula_1 | non-empty | False | True | agentar | 0.8808 | Stage-A 可修复但触发器未触发（非空/非报错） |
| 1010 | formula_1 | non-empty | False | False | omnisql | 0.8670 | 非空/非报错，ORM 未选对 |
| 1011 | formula_1 | non-empty | False | False | agentar | 0.7773 | 非空/非报错，ORM 未选对 |
| 1014 | formula_1 | non-empty | False | True | omnisql-921 | 0.5312 | Stage-A 可修复但触发器未触发（非空/非报错） |
| 1021 | european_football_2 | non-empty | False | False | agentar | 0.9466 | 非空/非报错，ORM 未选对 |
| 1023 | european_football_2 | non-empty | False | False | omnisql-921 | 0.8670 | 非空/非报错，ORM 未选对 |
| 1027 | european_football_2 | non-empty | False | False | omnisql | 0.5312 | 非空/非报错，ORM 未选对 |
| 1028 | european_football_2 | non-empty | False | False | qwen3 | 0.9149 | 非空/非报错，ORM 未选对 |
| 1029 | european_football_2 | non-empty | False | False | agentar | 0.8520 | 非空/非报错，ORM 未选对 |
| 1041 | european_football_2 | empty | True | False | omnisql-921 | 0.5927 | 触发但 ORM 选择仍错 |
| 1060 | european_football_2 | non-empty | False | True | agentar | 0.8176 | Stage-A 可修复但触发器未触发（非空/非报错） |
| 1064 | european_football_2 | non-empty | False | False | omnisql | 0.8933 | 非空/非报错，ORM 未选对 |
| 1091 | european_football_2 | non-empty | False | False | agentar | 0.9149 | 非空/非报错，ORM 未选对 |
| 1108 | european_football_2 | empty | True | True | agentar | 0.8670 | Stage-A 修复且最终触发也修复 |
| 1113 | european_football_2 | non-empty | False | False | omnisql | 0.8808 | 非空/非报错，ORM 未选对 |
| 1144 | european_football_2 | non-empty | False | False | agentar | 0.8808 | 非空/非报错，ORM 未选对 |
| 1152 | thrombosis_prediction | non-empty | False | False | omnisql | 0.4073 | 非空/非报错，ORM 未选对 |
| 1168 | thrombosis_prediction | empty | True | True | omnisql-921 | 0.5000 | Stage-A 修复且最终触发也修复 |
| 1172 | thrombosis_prediction | non-empty | False | False | agentar | 0.8670 | 非空/非报错，ORM 未选对 |
| 1177 | thrombosis_prediction | non-empty | False | False | omnisql-921 | 0.8808 | 非空/非报错，ORM 未选对 |
| 1178 | thrombosis_prediction | non-empty | False | True | agentar | 0.9149 | Stage-A 可修复但触发器未触发（非空/非报错） |
| 1193 | thrombosis_prediction | non-empty | False | True | agentar | 0.8355 | Stage-A 可修复但触发器未触发（非空/非报错） |
| 1197 | thrombosis_prediction | non-empty | False | False | omnisql | 0.9149 | 非空/非报错，ORM 未选对 |
| 1199 | thrombosis_prediction | non-empty | False | False | agentar | 0.6514 | 非空/非报错，ORM 未选对 |
| 1219 | thrombosis_prediction | non-empty | False | False | omnisql-921 | 0.3208 | 非空/非报错，ORM 未选对 |
| 1229 | thrombosis_prediction | non-empty | False | False | agentar | 0.7549 | 非空/非报错，ORM 未选对 |
| 1233 | thrombosis_prediction | non-empty | False | False | omnisql | 0.3775 | 非空/非报错，ORM 未选对 |
| 1243 | thrombosis_prediction | non-empty | False | False | qwen3 | 0.3486 | 非空/非报错，ORM 未选对 |
| 1247 | thrombosis_prediction | non-empty | False | False | omnisql-921 | 0.7549 | 非空/非报错，ORM 未选对 |
| 1248 | thrombosis_prediction | non-empty | False | False | omnisql | 0.7773 | 非空/非报错，ORM 未选对 |
| 1252 | thrombosis_prediction | non-empty | False | True | agentar | 0.8176 | Stage-A 可修复但触发器未触发（非空/非报错） |
| 1256 | thrombosis_prediction | non-empty | False | True | agentar | 0.5622 | Stage-A 可修复但触发器未触发（非空/非报错） |
| 1257 | thrombosis_prediction | non-empty | False | False | omnisql-921 | 0.2942 | 非空/非报错，ORM 未选对 |
| 1259 | thrombosis_prediction | empty | True | False | omnisql | 0.1480 | 触发但 ORM 选择仍错 |
| 1265 | thrombosis_prediction | non-empty | False | False | agentar | 0.3486 | 非空/非报错，ORM 未选对 |
| 1268 | thrombosis_prediction | non-empty | False | False | omnisql | 0.4688 | 非空/非报错，ORM 未选对 |
| 1269 | thrombosis_prediction | empty | True | False | omnisql-921 | 0.2227 | 触发但 ORM 选择仍错 |
| 1273 | thrombosis_prediction | non-empty | False | False | omnisql | 0.3208 | 非空/非报错，ORM 未选对 |
| 1275 | thrombosis_prediction | non-empty | False | False | agentar | 0.4688 | 非空/非报错，ORM 未选对 |
| 1279 | thrombosis_prediction | non-empty | False | False | omnisql | 0.2689 | 非空/非报错，ORM 未选对 |
| 1280 | thrombosis_prediction | non-empty | False | True | agentar | 0.8670 | Stage-A 可修复但触发器未触发（非空/非报错） |
| 1290 | thrombosis_prediction | non-empty | False | False | omnisql | 0.7311 | 非空/非报错，ORM 未选对 |
| 1291 | thrombosis_prediction | non-empty | False | False | agentar | 0.7549 | 非空/非报错，ORM 未选对 |
| 1298 | thrombosis_prediction | non-empty | False | True | agentar | 0.8176 | Stage-A 可修复但触发器未触发（非空/非报错） |
| 1306 | thrombosis_prediction | non-empty | False | True | agentar | 0.7773 | Stage-A 可修复但触发器未触发（非空/非报错） |
| 1314 | student_club | empty | True | True | agentar | 0.8933 | Stage-A 修复且最终触发也修复 |
| 1322 | student_club | non-empty | False | False | agentar | 0.8808 | 非空/非报错，ORM 未选对 |
| 1352 | student_club | non-empty | False | False | agentar | 0.9579 | 非空/非报错，ORM 未选对 |
| 1370 | student_club | non-empty | False | False | omnisql | 0.9047 | 非空/非报错，ORM 未选对 |
| 1391 | student_club | non-empty | False | True | qwen3 | 0.6514 | Stage-A 可修复但触发器未触发（非空/非报错） |
| 1425 | student_club | non-empty | False | False | agentar | 0.9466 | 非空/非报错，ORM 未选对 |
| 1441 | student_club | non-empty | False | False | agentar | 0.9399 | 非空/非报错，ORM 未选对 |
| 1446 | student_club | non-empty | False | False | agentar | 0.9399 | 非空/非报错，ORM 未选对 |
| 1453 | student_club | empty | True | True | omnisql-921 | 0.3486 | Stage-A 修复且最终触发也修复 |
| 1467 | student_club | non-empty | False | True | agentar | 0.7311 | Stage-A 可修复但触发器未触发（非空/非报错） |
| 1468 | student_club | empty | True | False | omnisql | 0.5000 | 触发但 ORM 选择仍错 |
| 1482 | debit_card_specializing | non-empty | False | False | omnisql-921 | 0.0953 | 非空/非报错，ORM 未选对 |
| 1491 | debit_card_specializing | non-empty | False | False | agentar | 0.9149 | 非空/非报错，ORM 未选对 |
| 1496 | debit_card_specializing | non-empty | False | True | qwen3 | 0.8933 | Stage-A 可修复但触发器未触发（非空/非报错） |
| 1498 | debit_card_specializing | non-empty | False | False | agentar | 0.9047 | 非空/非报错，ORM 未选对 |
| 1503 | debit_card_specializing | non-empty | False | False | omnisql | 0.6225 | 非空/非报错，ORM 未选对 |
| 1520 | debit_card_specializing | non-empty | False | False | omnisql-921 | 0.2451 | 非空/非报错，ORM 未选对 |
