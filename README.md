# Technical Recruiter Sourcing Toolkit (demo)

pip install requests pypdf python-docx

1. boolean_builder.py  - role -> LinkedIn / Google X-ray / GitHub search strings (含台灣地點、中英同義詞)
2. resume_screen.py    - 履歷 (.txt/.pdf/.docx) -> skills 抽取 -> 加權評分 -> 可解釋排名 CSV
3. github_sourcer.py   - 官方 GitHub API 找公開 profile，依 repo/stars/活躍度排序 (需在可連外網的機器跑)
skills_taxonomy.py     - 技能同義詞表，直接擴充即可

Compliance: 不爬 LinkedIn/104；只用官方 API、自家 ATS 匯出、或候選人同意的資料；遵守 PDPA，提供 opt-out。
