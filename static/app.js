const { useState, useEffect, useRef, useCallback, useMemo } = React;

// ── Icons ─────────────────────────────────────────────────────────────────────
const I = {
    Car: () => <svg viewBox="0 0 24 24" width="16" height="16" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><rect x="1" y="3" width="15" height="13" rx="2"/><path d="m16 8 4 1 3 3v5h-7V8Z"/><circle cx="5.5" cy="18.5" r="2.5"/><circle cx="18.5" cy="18.5" r="2.5"/></svg>,
    Search: () => <svg viewBox="0 0 24 24" width="14" height="14" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round"><circle cx="11" cy="11" r="8"/><path d="m21 21-4.3-4.3"/></svg>,
    Sliders: () => <svg viewBox="0 0 24 24" width="14" height="14" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><line x1="4" y1="21" x2="4" y2="14"/><line x1="4" y1="10" x2="4" y2="3"/><line x1="12" y1="21" x2="12" y2="12"/><line x1="12" y1="8" x2="12" y2="3"/><line x1="20" y1="21" x2="20" y2="16"/><line x1="20" y1="12" x2="20" y2="3"/><line x1="1" y1="14" x2="7" y2="14"/><line x1="9" y1="8" x2="15" y2="8"/><line x1="17" y1="16" x2="23" y2="16"/></svg>,
    ChevronDown: ({ open }) => <svg viewBox="0 0 24 24" width="14" height="14" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round" style={{ transition:'transform 0.2s', transform: open ? 'rotate(180deg)' : 'rotate(0)' }}><path d="m6 9 6 6 6-6"/></svg>,
    Link: () => <svg viewBox="0 0 24 24" width="11" height="11" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round"><path d="M18 13v6a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2h6"/><polyline points="15 3 21 3 21 9"/><line x1="10" y1="14" x2="21" y2="3"/></svg>,
    Gauge: () => <svg viewBox="0 0 24 24" width="11" height="11" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="m12 14 4-4"/><path d="M3.34 19a10 10 0 1 1 17.32 0"/></svg>,
    Calendar: () => <svg viewBox="0 0 24 24" width="11" height="11" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><rect x="3" y="4" width="18" height="18" rx="2"/><line x1="16" y1="2" x2="16" y2="6"/><line x1="8" y1="2" x2="8" y2="6"/><line x1="3" y1="10" x2="21" y2="10"/></svg>,
    MapPin: () => <svg viewBox="0 0 24 24" width="11" height="11" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M20 10c0 4.993-5.539 10.193-7.399 11.799a1 1 0 0 1-1.202 0C9.539 20.193 4 14.993 4 10a8 8 0 0 1 16 0"/><circle cx="12" cy="10" r="3"/></svg>,
    Fuel: () => <svg viewBox="0 0 24 24" width="11" height="11" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M3 22V6a2 2 0 0 1 2-2h8a2 2 0 0 1 2 2v16"/><path d="M2 22h14"/><path d="M15 6h3a2 2 0 0 1 2 2v3a2 2 0 0 1-2 2h-3"/></svg>,
    X: () => <svg viewBox="0 0 24 24" width="12" height="12" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round"><path d="M18 6 6 18M6 6l12 12"/></svg>,
    Loader: () => <svg className="spin" viewBox="0 0 24 24" width="14" height="14" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round"><path d="M21 12a9 9 0 1 1-6.219-8.56"/></svg>,
    TrendUp: () => <svg viewBox="0 0 24 24" width="13" height="13" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><polyline points="22 7 13.5 15.5 8.5 10.5 2 17"/><polyline points="16 7 22 7 22 13"/></svg>,
};

// ── Helpers ───────────────────────────────────────────────────────────────────
const fmtPrice = p => p ? Math.round(p).toLocaleString("fr-FR") + " €" : "N/A";
const fmtKm    = km => { const n = parseInt(String(km).replace(/\D/g,""))||0; return n>0 ? n.toLocaleString("fr-FR")+" km" : "N/A"; };

const SCORE_CFG = score =>
    score >= 75 ? { label:"Top Deal",      emoji:"🔥", color:"#22c55e", bg:"rgba(34,197,94,0.1)",   border:"rgba(34,197,94,0.25)"  } :
    score >= 55 ? { label:"Bonne Affaire", emoji:"⭐", color:"#60a5fa", bg:"rgba(96,165,250,0.1)",  border:"rgba(96,165,250,0.25)" } :
    score >= 35 ? { label:"Correct",       emoji:"",   color:"#f59e0b", bg:"rgba(245,158,11,0.1)",  border:"rgba(245,158,11,0.25)" } :
                  { label:"Standard",      emoji:"",   color:"#334155", bg:"rgba(51,65,85,0.1)",    border:"rgba(51,65,85,0.3)"    };

const SOURCE_COLOR = { "2ememain":"#f97316", "2dehands":"#a78bfa", "AutoScout24":"#3b82f6" };

// ── Score Ring ────────────────────────────────────────────────────────────────
const ScoreRing = ({ score }) => {
    const r = 14, circ = 2 * Math.PI * r;
    const { color } = SCORE_CFG(score);
    return (
        <div style={{ position:"relative", width:36, height:36 }}>
            <svg viewBox="0 0 36 36" style={{ width:36, height:36, transform:"rotate(-90deg)" }}>
                <circle cx="18" cy="18" r={r} fill="none" stroke="rgba(255,255,255,0.06)" strokeWidth="3"/>
                <circle cx="18" cy="18" r={r} fill="none" stroke={color} strokeWidth="3"
                    strokeDasharray={circ} strokeDashoffset={circ-(score/100)*circ} strokeLinecap="round"/>
            </svg>
            <span style={{ position:"absolute", inset:0, display:"flex", alignItems:"center", justifyContent:"center",
                fontSize:10, fontWeight:700, color }}>{score}</span>
        </div>
    );
};

// ── Skeleton ──────────────────────────────────────────────────────────────────
const SkeletonCard = () => (
    <div className="cw-card">
        <div className="skeleton" style={{ height:185 }}/>
        <div style={{ padding:14, display:"flex", flexDirection:"column", gap:10 }}>
            <div className="skeleton" style={{ height:10, width:"35%" }}/>
            <div className="skeleton" style={{ height:13, width:"90%" }}/>
            <div className="skeleton" style={{ height:13, width:"70%" }}/>
            <div style={{ display:"grid", gridTemplateColumns:"1fr 1fr", gap:6 }}>
                {[...Array(4)].map((_,i)=><div key={i} className="skeleton" style={{ height:9 }}/>)}
            </div>
            <div className="skeleton" style={{ height:30, borderRadius:7 }}/>
        </div>
    </div>
);

// ── Car Card ──────────────────────────────────────────────────────────────────
const CarCard = ({ car }) => {
    const score = Math.round(car.deal_score || 0);
    const sc    = SCORE_CFG(score);

    return (
        <div className="cw-card">
            <div className="cw-card-img">
                {car.image
                    ? <img src={car.image} alt={car.title} loading="lazy"/>
                    : <div className="cw-no-img">
                        <I.Car/>
                        <span>Pas d'image</span>
                      </div>
                }
                <div className="cw-card-img-fade"/>
                <span className="cw-badge-source">{car.source}</span>
                <span className="cw-badge-price">{fmtPrice(car.price)}</span>
                <div className="cw-score-wrap"><ScoreRing score={score}/></div>
            </div>

            <div className="cw-card-body">
                <span className="cw-deal-badge" style={{ color:sc.color, background:sc.bg, borderColor:sc.border }}>
                    {sc.emoji && sc.emoji+" "}{sc.label}
                </span>

                <p className="cw-card-title">{car.title}</p>

                <div className="cw-card-specs">
                    {[
                        [<I.Calendar/>, car.year || "?"],
                        [<I.Gauge/>,    fmtKm(car.km)],
                        [<I.Fuel/>,     car.fuel_type || "—"],
                        [<I.MapPin/>,   car.city || "—"],
                    ].map(([icon, val], i) => (
                        <div key={i} className="cw-spec">{icon}<span>{val}</span></div>
                    ))}
                </div>

                <a href={car.url} target="_blank" rel="noopener noreferrer" className="cw-card-cta">
                    Voir l'annonce <I.Link/>
                </a>
            </div>
        </div>
    );
};

// ── Stats ─────────────────────────────────────────────────────────────────────
const Stats = ({ results }) => {
    const total  = results.length;
    const top    = results.filter(r => (r.deal_score||0) >= 75).length;
    const avgPx  = total > 0 ? Math.round(results.reduce((s,r)=>s+(r.price||0),0)/total) : 0;
    const counts = results.reduce((acc,r)=>{ acc[r.source]=(acc[r.source]||0)+1; return acc; }, {});

    return (
        <div className="cw-stats">
            <div className="cw-stat">
                <span className="cw-stat-val">{total}</span>
                <span className="cw-stat-label">annonces</span>
            </div>
            <span className="cw-stat-sep">|</span>
            <div className="cw-stat">
                <span className="cw-stat-val" style={{ color:"#22c55e" }}>{top}</span>
                <span className="cw-stat-label">top deals</span>
            </div>
            <span className="cw-stat-sep">|</span>
            <div className="cw-stat">
                <span className="cw-stat-val">{avgPx > 0 ? fmtPrice(avgPx) : "—"}</span>
                <span className="cw-stat-label">prix moyen</span>
            </div>
            <span className="cw-stat-sep">|</span>
            {/* Always show all 3 sources, greyed out if 0 */}
            {ALL_SOURCES.map(s => {
                const n   = counts[s.key] || 0;
                const dim = n === 0;
                return (
                    <div key={s.key} className="cw-stat" title={dim ? `Aucune annonce trouvée sur ${s.label}` : ""}>
                        <span className="cw-source-dot" style={{ background: dim ? "#1e293b" : s.color }}/>
                        <span className="cw-stat-val" style={{ color: dim ? "#1e2d40" : undefined }}>{n}</span>
                        <span className="cw-stat-label" style={{ color: dim ? "#1a2535" : undefined }}>{s.label}</span>
                        {dim && <span style={{ fontSize:10, color:"#1e2d40" }}>— 0 résultat</span>}
                    </div>
                );
            })}
        </div>
    );
};

// ── Toolbar ───────────────────────────────────────────────────────────────────
const ALL_SOURCES = [
    { key:"2ememain",    label:"2ememain",    color:"#f97316" },
    { key:"2dehands",    label:"2dehands",    color:"#a78bfa" },
    { key:"AutoScout24", label:"AutoScout24", color:"#3b82f6" },
];

const Toolbar = ({ sort, setSort, source, setSource, results, count }) => {
    const SORTS = [
        { k:"score",      l:"Score"  },
        { k:"price_asc",  l:"Prix ↑" },
        { k:"price_desc", l:"Prix ↓" },
        { k:"year_desc",  l:"Année"  },
        { k:"km_asc",     l:"KM"     },
    ];

    return (
        <div style={{ marginBottom:20 }}>
            {/* Row 1 — sort */}
            <div className="cw-toolbar" style={{ marginBottom:10 }}>
                <div className="cw-toolbar-left">
                    <span style={{ fontSize:11, color:"#334155", fontWeight:600 }}>TRIER</span>
                    <div className="cw-toolbar-sep"/>
                    {SORTS.map(o => (
                        <button key={o.k} className={`btn-pill${sort===o.k?" active":""}`} onClick={()=>setSort(o.k)}>
                            {o.l}
                        </button>
                    ))}
                </div>
                {count > 0 && <span className="cw-count">{count} résultat{count>1?"s":""}</span>}
            </div>

            {/* Row 2 — source filter — always visible */}
            <div style={{ display:"flex", alignItems:"center", gap:8, flexWrap:"wrap" }}>
                <span style={{ fontSize:11, color:"#334155", fontWeight:600 }}>SITE</span>
                <div className="cw-toolbar-sep"/>
                <button className={`btn-pill${source==="all"?" active":""}`} onClick={()=>setSource("all")}>
                    Tous {results.length > 0 && <span style={{ opacity:0.5, fontSize:10 }}>({results.length})</span>}
                </button>
                {ALL_SOURCES.map(s => {
                    const n = results.filter(r=>r.source===s.key).length;
                    return (
                        <button key={s.key}
                            className={`btn-pill${source===s.key?" active":""}`}
                            onClick={()=>setSource(s.key)}
                            style={{ display:"flex", alignItems:"center", gap:5 }}>
                            <span className="cw-source-dot" style={{ background: s.color }}/>
                            {s.label}
                            <span style={{ opacity:0.45, fontSize:10 }}>({n})</span>
                        </button>
                    );
                })}
            </div>
        </div>
    );
};

// ── Filter Panel ──────────────────────────────────────────────────────────────
const FilterPanel = ({ config, onChange, onSearch, isLoading }) => {
    const [open, setOpen] = useState(true);

    const activeCount = ["make","price_max","km_max","year_min","fuel","transmission","region","exclude"]
        .filter(k => config[k] && config[k] !== "").length;

    const numSel = (label, name, opts) => (
        <div className="cw-field">
            <label>{label}</label>
            <select className="cw-select" name={name} value={config[name]||opts[0][0]}
                onChange={e => onChange(prev => ({ ...prev, [name]: Number(e.target.value) }))}>
                {opts.map(([v,l]) => <option key={v} value={v}>{l}</option>)}
            </select>
        </div>
    );

    const inp = (label, name, type="text", ph="") => (
        <div className="cw-field">
            <label>{label}</label>
            <input className="cw-input" type={type} name={name} placeholder={ph}
                value={config[name]||""}
                onChange={e => onChange(prev => ({
                    ...prev,
                    [name]: ["price_min","price_max","year_min","km_max"].includes(name)
                        ? (e.target.value===""?"":Number(e.target.value)) : e.target.value
                }))}
            />
        </div>
    );

    const sel = (label, name, opts) => (
        <div className="cw-field">
            <label>{label}</label>
            <select className="cw-select" name={name} value={config[name]||""}
                onChange={e => onChange(prev => ({ ...prev, [name]: e.target.value }))}>
                {opts.map(([v,l]) => <option key={v} value={v}>{l}</option>)}
            </select>
        </div>
    );

    return (
        <div className="cw-panel">
            <div className="cw-panel-header" onClick={()=>setOpen(o=>!o)}>
                <div className="cw-panel-title">
                    <I.Sliders/>
                    <span>Filtres</span>
                    {activeCount > 0 && (
                        <span className="cw-filter-tag">{activeCount} actif{activeCount>1?"s":""}</span>
                    )}
                </div>
                <I.ChevronDown open={open}/>
            </div>

            {open && <>
                <hr className="cw-panel-divider"/>
                <div className="cw-panel-body">
                    <div className="cw-filter-grid">
                        {inp("Marque",       "make",      "text",   "BMW, Golf…")}
                        {inp("Budget max €", "price_max", "number", "10 000")}
                        {inp("KM max",       "km_max",    "number", "150 000")}
                        {inp("Année min",    "year_min",  "number", "2015")}
                        {inp("Région",       "region",    "text",   "Liège, BXL…")}
                        {config.region && numSel("Rayon", "radius_km", [
                            [10,"10 km"], [25,"25 km"], [50,"50 km"], [100,"100 km"],
                        ])}
                        {inp("Exclure", "exclude", "text", "leaseplan, arval…")}
                        {sel("Carburant", "fuel", [
                            ["","Tous"], ["essence","Essence"], ["diesel","Diesel"],
                            ["hybride","Hybride"], ["electrique","Électrique"],
                        ])}
                        {sel("Boîte", "transmission", [
                            ["","Toutes"], ["manuelle","Manuelle"], ["automatique","Automatique"],
                        ])}
                    </div>
                    <div className="cw-filter-actions">
                        <button className="btn-ghost" onClick={()=>onChange(prev=>({
                            ...prev, make:"", price_max:"", km_max:"", year_min:"", region:"", radius_km:25, exclude:"", fuel:"", transmission:""
                        }))}>
                            <I.X/> Réinitialiser
                        </button>
                        <button className="btn-primary" onClick={onSearch} disabled={isLoading}>
                            {isLoading ? <><I.Loader/> Recherche…</> : <><I.Search/> Chercher</>}
                        </button>
                    </div>
                </div>
            </>}
        </div>
    );
};

// ── Header ────────────────────────────────────────────────────────────────────
const Header = ({ isLoading }) => (
    <header className="cw-header">
        <div className="cw-header-inner">
            <div className="cw-logo">
                <div className="cw-logo-icon"><I.Car/></div>
                <span className="cw-logo-text">Car<span>Watch</span></span>
            </div>
            <div className="cw-status">
                <span className={`cw-status-dot${isLoading?" loading":" active"}`}/>
                {isLoading ? "Scraping…" : "En ligne"}
            </div>
        </div>
    </header>
);

// ── Toast ─────────────────────────────────────────────────────────────────────
const Toast = ({ msg, type }) => <div className={`cw-toast ${type}`}>{msg}</div>;

// ── Empty State ───────────────────────────────────────────────────────────────
const Empty = () => (
    <div className="cw-empty">
        <div className="cw-empty-icon">
            <svg viewBox="0 0 24 24" width="24" height="24" fill="none" stroke="currentColor" strokeWidth="1.5">
                <circle cx="11" cy="11" r="8"/><path d="m21 21-4.3-4.3"/>
            </svg>
        </div>
        <h3>Aucun résultat</h3>
        <p>Modifie tes filtres et relance une recherche pour trouver les meilleures affaires.</p>
    </div>
);

// ── App ───────────────────────────────────────────────────────────────────────
const App = () => {
    const [config,    setConfig]    = useState(null);
    const [results,   setResults]   = useState([]);
    const [isLoading, setIsLoading] = useState(false);
    const [sort,      setSort]      = useState("score");
    const [source,    setSource]    = useState("all");
    const [toast,     setToast]     = useState(null);
    const timer = useRef(null);

    const showToast = useCallback((msg, type="success") => {
        setToast({ msg, type });
        clearTimeout(timer.current);
        timer.current = setTimeout(() => setToast(null), 3200);
    }, []);

    useEffect(() => {
        fetch("/api/config").then(r=>r.json()).then(setConfig)
            .catch(()=>showToast("Erreur de chargement","error"));
    }, []);

    const sorted = useMemo(() => {
        const arr = source==="all" ? [...results] : results.filter(r=>r.source===source);
        switch (sort) {
            case "price_asc":  return arr.sort((a,b)=>(a.price||0)-(b.price||0));
            case "price_desc": return arr.sort((a,b)=>(b.price||0)-(a.price||0));
            case "year_desc":  return arr.sort((a,b)=>parseInt(b.year||0)-parseInt(a.year||0));
            case "km_asc":     return arr.sort((a,b)=>{
                const ka=parseInt(String(a.km||"0").replace(/\D/g,""))||0;
                const kb=parseInt(String(b.km||"0").replace(/\D/g,""))||0;
                return ka-kb;
            });
            default:           return arr.sort((a,b)=>(b.deal_score||0)-(a.deal_score||0));
        }
    }, [results, sort, source]);

    const handleSearch = useCallback(async (cfg=config) => {
        if (!cfg) return;
        setIsLoading(true);
        try {
            const apiKey = window.__API_KEY || "";
            await fetch("/api/config", {
                method:"POST",
                headers:{"Content-Type":"application/json", "X-Api-Key": apiKey},
                body:JSON.stringify(cfg),
            });
            const res = await fetch("/api/search", { headers: {"X-Api-Key": apiKey} });
            const data = await res.json();
            if (data.status==="success") {
                setResults(data.results||[]);
                setSource("all");
                showToast(`${data.count} annonce${data.count!==1?"s":""} trouvée${data.count!==1?"s":""} !`);
            } else {
                showToast("Erreur lors de la recherche.","error");
            }
        } catch(e) {
            showToast("Erreur réseau.","error");
        } finally {
            setIsLoading(false);
        }
    }, [config, showToast]);

    if (!config) return (
        <div style={{ minHeight:"100vh", display:"flex", alignItems:"center", justifyContent:"center", flexDirection:"column", gap:12 }}>
            <div style={{ width:36,height:36,borderRadius:"50%",border:"2px solid rgba(34,197,94,0.2)",borderTopColor:"#22c55e" }} className="spin"/>
            <span style={{ fontSize:13,color:"#334155" }}>Chargement…</span>
        </div>
    );

    return (
        <>
            <Header isLoading={isLoading}/>
            <main className="cw-main">

                <div className="cw-hero">
                    <h1>Radar <span className="cw-accent">Achat & Revente</span></h1>
                    <p>2ememain · 2dehands · AutoScout24 — Belgique</p>
                </div>

                <FilterPanel config={config} onChange={setConfig}
                    onSearch={()=>handleSearch(config)} isLoading={isLoading}/>

                <Toolbar sort={sort} setSort={setSort} source={source} setSource={setSource}
                    results={results} count={sorted.length}/>

                {isLoading ? (
                    <div className="cw-grid">
                        {[...Array(8)].map((_,i)=><SkeletonCard key={i}/>)}
                    </div>
                ) : sorted.length > 0 ? (
                    <>
                        <Stats results={results}/>
                        <div className="cw-grid">
                            {sorted.map((car,i)=><CarCard key={`${car.id}-${i}`} car={car}/>)}
                        </div>
                    </>
                ) : (
                    <Empty/>
                )}

            </main>

            {toast && <Toast msg={toast.msg} type={toast.type}/>}
        </>
    );
};

ReactDOM.createRoot(document.getElementById("root")).render(<App/>);
