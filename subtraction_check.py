# Independent re-implementation of the 4-phase subtraction mechanism
# built ONLY from the KB node text, to check its logical claims.

def bits(n):
    """LSB->MSB bit list, no padding. n>=1."""
    out=[]
    while n: out.append(n&1); n>>=1
    return out

def four_phase(a, b):
    """Returns (negative, magnitude) per the node's phases."""
    A, B = bits(a), bits(b)
    frontier = len(A)-1          # left MSB index, always bit 1

    # PHASE 1: plain borrow subtraction LSB->MSB over low bits (below frontier)
    res=[]; borrow=0
    for i in range(frontier):
        bi = B[i] if i < len(B) else 0
        d = A[i] - bi - borrow
        res.append(d & 1)
        borrow = 1 if d < 0 else 0
    b1 = borrow

    right_here = B[frontier] if frontier < len(B) else 0
    right_multibit = len(B) > len(A)

    # activation trigger (C4)
    negative_trigger = right_multibit or (right_here==1 and b1==1)

    if not negative_trigger:
        # positive path: process left MSB normally
        d = 1 - right_here - b1
        res.append(d & 1)
        assert d >= 0, "positive path got standing borrow!"
        mag = sum(bit<<i for i,bit in enumerate(res))
        return (False, mag)

    # PHASE 2: negate phase-1 result bits in place, 0 - bit - rb
    rb=0
    for i in range(frontier):
        d = 0 - res[i] - rb
        res[i] = d & 1
        rb = 1 if d < 0 else 0
    b2 = rb

    # PHASE 3: frontier column via table keyed (right_here, b1, b2)
    table = {(0,0,0):(1,1), (0,0,1):(0,1), (0,1,1):(1,1),
             (1,0,0):(0,0), (1,0,1):(1,1), (1,1,1):(0,0)}
    key = (right_here, b1, b2)
    if key not in table:
        return ("UNREACHABLE_KEY", key)
    out_bit, borrow_out = table[key]
    res.append(out_bit)
    # overhang: remaining right bits as rightbit - borrow
    for i in range(frontier+1, len(B)):
        d = B[i] - borrow_out
        res.append(d & 1)
        borrow_out = 1 if d < 0 else 0

    # PHASE 4: drain leading zeros
    while len(res)>1 and res[-1]==0: res.pop()
    mag = sum(bit<<i for i,bit in enumerate(res))
    return (True, mag)

# ---- C1 + C4: full sweep, wider than the node's (1..127 -> 1..255) ----
fails=[]; trig_fails=[]
for a in range(1,256):
    for b in range(1,256):
        neg, mag = four_phase(a,b)
        if neg=="UNREACHABLE_KEY": fails.append((a,b,neg,mag)); continue
        exp_neg, exp_mag = (a<b), abs(a-b)
        # a==b: node routes to positive/zero path
        if (neg,mag) != (exp_neg,exp_mag): fails.append((a,b,neg,mag,exp_neg,exp_mag))
print("C1 sweep 1..255 both signs: failures =", len(fails), fails[:5])

# ---- C2: independently re-derive frontier table from ground truth ----
derived={}
for a in range(1,256):
    for b in range(1,256):
        if a>=b: continue
        A,B=bits(a),bits(b)
        f=len(A)-1
        if len(B)>len(A): continue    # table only governs same-length frontier
        res=[];bo=0
        for i in range(f):
            bi=B[i] if i<len(B) else 0
            d=A[i]-bi-bo; res.append(d&1); bo=1 if d<0 else 0
        b1=bo; rh=B[f] if f<len(B) else 0
        if not (rh==1 and b1==1) and not len(B)>len(A):
            if not (rh==1 and b1==1): continue
        rb=0
        for i in range(f):
            d=0-res[i]-rb; res[i]=d&1; rb=1 if d<0 else 0
        b2=rb
        # brute force which (out,bout) gives correct magnitude
        good=[]
        for ob in (0,1):
            for bt in (0,1):
                r2=res[:f]+[ob]; bo2=bt
                for i in range(f+1,len(B)):
                    d=B[i]-bo2; r2.append(d&1); bo2=1 if d<0 else 0
                while len(r2)>1 and r2[-1]==0: r2.pop()
                if sum(x<<i for i,x in enumerate(r2))==b-a: good.append((ob,bt))
        k=(rh,b1,b2)
        derived.setdefault(k,set()).update(good)
node_table={(0,0,0):(1,1),(0,0,1):(0,1),(0,1,1):(1,1),(1,0,0):(0,0),(1,0,1):(1,1),(1,1,1):(0,0)}
print("C2 keys observed (same-length negative, config-2 route):")
for k,v in sorted(derived.items()):
    ok = node_table.get(k) in v if k in node_table else "KEY NOT IN NODE TABLE"
    print(" ", k, "valid outputs:", sorted(v), "| node entry consistent:", ok)

# ---- C3: reachability of (1,1,0) and (0,1,0) ----
seen=set()
for a in range(1,1024):
    for b in range(1,1024):
        if a>=b: continue
        A,B=bits(a),bits(b); f=len(A)-1
        res=[];bo=0
        for i in range(f):
            bi=B[i] if i<len(B) else 0
            d=A[i]-bi-bo; res.append(d&1); bo=1 if d<0 else 0
        b1=bo
        rb=0
        for i in range(f):
            d=0-res[i]-rb; res[i]=d&1; rb=1 if d<0 else 0
        seen.add((b1,rb))
print("C3 (b1,b2) pairs seen up to 1023:", sorted(seen), "-> (1,0) present:", (1,0) in seen)
