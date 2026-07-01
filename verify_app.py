c = open('app.py', encoding='utf-8').read()
find = ['id:\'strategy\'', 'playDebateFlow', 'unlockByAd', 'rd2', 
        'view-toggle', '/api/run', 'remainingCount', 'severity_pct', 
        '董事会辩论', '关键冲突', 'CEO 裁决', 'mockAgents', 'mockConflicts']
for f in find:
    print(f'{f[:30]:30s}: {"OK" if f in c else "MISSING"}')

# Count HTML features
print()
print('7 agents in BOARD:', c.count("id:'") >= 7)
print('Has ceo:', "'ceo'" in c)
print('Has graph nodes:', 'position:absolute' in c)
print('Has conflict bars:', 'conflict-track' in c)
print('Has ad unlock:', 'unlockByAd' in c)

# File size
print()
print('File size:', len(c))
