def bits(n):
    out=[]
    while n: out.append(n&1); n>>=1
    return out

derived={}
for a in range(1,512):
    for b in range(1,512):
        if a>=b: continue
        A,B=bits(a),bits(b); f=len(A)-1
        rh=B[f] if f<len(B) else 0
        res=[];bo=0
        for i in range(f):
            bi=B[i] if i<len(B) else 0
            d=A[i]-bi-bo; res.append(d&1); bo=1 if d<0 else 0
        b1=bo
        multibit=len(B)>len(A)
        if not (multibit or (rh==1 and b1==1)): continue   # both trigger configs
        rb=0
        for i in range(f):
            d=0-res[i]-rb; res[i]=d&1; rb=1 if d<0 else 0
        b2=rb
        good=set()
        for ob in (0,1):
            for bt in (0,1):
                r2=res[:f]+[ob]; bo2=bt
                for i in range(f+1,len(B)):
                    d=B[i]-bo2; r2.append(d&1); bo2=1 if d<0 else 0
                while len(r2)>1 and r2[-1]==0: r2.pop()
                if sum(x<<i for i,x in enumerate(r2))==b-a: good.add((ob,bt))
        derived.setdefault((rh,b1,b2),{'valid':set(),'n':0})
        e=derived[(rh,b1,b2)]
        e['valid'] = e['valid']&good if e['n'] else set(good)
        e['n']+=1

node={(0,0,0):(1,1),(0,0,1):(0,1),(0,1,1):(1,1),(1,0,0):(0,0),(1,0,1):(1,1),(1,1,1):(0,0)}
print(f"{'key':>10} {'cases':>6}  universally-valid outputs   node entry ok?")
for k in sorted(derived):
    e=derived[k]
    ok = node[k] in e['valid'] if k in node else "MISSING FROM NODE"
    print(f"{str(k):>10} {e['n']:>6}  {sorted(e['valid'])!s:26}  {ok}")
missing = set(node)-set(derived)
print("node keys never observed:", missing if missing else "none")
