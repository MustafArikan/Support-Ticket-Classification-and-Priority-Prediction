import { useState, useEffect, useRef } from 'react';
import axios from 'axios';
import { Send, CheckCircle, AlertCircle, AlertTriangle, Settings, Upload, Activity, Download, Moon, Sun, Globe, ChevronLeft, ChevronRight, Beaker, LayoutDashboard, Box, ExternalLink, Server, Zap } from 'lucide-react';
import Papa from 'papaparse';

const API_URL = 'http://localhost:8000'; 

function App() {
  const [text, setText] = useState('');
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<any>(null);
  const [health, setHealth] = useState<string>('checking');
  const [error, setError] = useState('');
  const [activeTab, setActiveTab] = useState<'single' | 'batch' | 'history'>('single');
  
  // UI States
  const [theme, setTheme] = useState<'light' | 'dark'>('light');
  const [lang, setLang] = useState<'tr' | 'en'>('tr');
  const [sidebarOpen, setSidebarOpen] = useState(true);
  const [modalData, setModalData] = useState<any>(null);

  // Batch states
  const fileInputRef = useRef<HTMLInputElement>(null);
  const [batchResults, setBatchResults] = useState<any[]>([]);
  const [batchProgress, setBatchProgress] = useState({ current: 0, total: 0 });
  const [isBatching, setIsBatching] = useState(false);

  // History state
  const [history, setHistory] = useState<any[]>(() => {
    try {
      return JSON.parse(localStorage.getItem('ticketHistory') || '[]');
    } catch {
      return [];
    }
  });

  useEffect(() => {
    localStorage.setItem('ticketHistory', JSON.stringify(history));
  }, [history]);

  useEffect(() => {
    if (theme === 'dark') {
      document.documentElement.classList.add('dark');
    } else {
      document.documentElement.classList.remove('dark');
    }
  }, [theme]);

  useEffect(() => {
    axios.get(`${API_URL}/health`)
      .then(() => setHealth('ok'))
      .catch(() => setHealth('error'));
  }, []);

  const handleAnalyze = async () => {
    if (text.trim().length === 0) {
      setError(lang === 'tr' ? 'Lütfen bir metin girin.' : 'Please enter some text.');
      return;
    }
    setError('');
    setLoading(true);
    try {
      const res = await axios.post(`${API_URL}/api/v1/tickets/predict`, { text });
      setResult(res.data);
      
      const newEntry = {
        text,
        category: res.data.category,
        priority: res.data.priority,
        confidence: res.data.confidence,
        date: new Date().toISOString()
      };
      setHistory(prev => [newEntry, ...prev].slice(0, 15));
      
    } catch (err: any) {
      setError(err.response?.data?.detail?.[0]?.msg || err.response?.data?.detail || (lang === 'tr' ? 'Sunucu hatası' : 'Server error'));
    } finally {
      setLoading(false);
    }
  };

  const handleStartService = (service: string, url: string) => {
    axios.post(`${API_URL}/api/v1/system/start`, { service })
      .catch(err => console.error("Service start error:", err));
    window.open(url, '_blank');
  };

  const processBatchFile = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;

    setIsBatching(true);
    setBatchResults([]);
    setError('');

    try {
      const textContent = await file.text();
      let lines: string[] = [];

      if (file.name.endsWith('.csv')) {
        const parsed = Papa.parse(textContent, { header: true, skipEmptyLines: true });
        if (parsed.data.length > 0) {
          const firstRow = parsed.data[0] as Record<string, string>;
          let textCol = Object.keys(firstRow).find(c => ['body', 'text', 'description', 'talepler', 'mesaj', 'icerik'].includes(c.toLowerCase()));
          if (!textCol) textCol = Object.keys(firstRow)[0];
          
          lines = (parsed.data as any[]).map(row => row[textCol!]).filter(t => t && String(t).trim().length > 0);
        }
      } else {
        lines = textContent.split('\n').filter(line => line.trim().length > 0);
      }

      setBatchProgress({ current: 0, total: lines.length });
      
      const results = [];
      for (let i = 0; i < lines.length; i++) {
        setBatchProgress(prev => ({ ...prev, current: i + 1 }));
        try {
          const res = await axios.post(`${API_URL}/api/v1/tickets/predict`, { text: lines[i].substring(0, 5000) });
          results.push({
            Text: lines[i],
            Category: res.data.category,
            Priority: res.data.priority,
            Confidence: `${(res.data.confidence * 100).toFixed(1)}%`
          });
          
          const newEntry = {
            text: lines[i],
            category: res.data.category,
            priority: res.data.priority,
            confidence: res.data.confidence,
            date: new Date().toISOString()
          };
          setHistory(prev => [newEntry, ...prev].slice(0, 15));
          
        } catch (err: any) {
          const errMsg = err.response?.data?.detail?.[0]?.msg || 'Error';
          results.push({ Text: lines[i], Category: lang === 'tr' ? `Hata: ${errMsg}` : `Error: ${errMsg}`, Priority: '-', Confidence: '-' });
        }
        setBatchResults([...results]);
      }
    } catch (err) {
      setError(lang === 'tr' ? 'Dosya işlenemedi.' : 'Failed to process file.');
    } finally {
      setIsBatching(false);
      if (fileInputRef.current) fileInputRef.current.value = '';
    }
  };

  const downloadCSV = () => {
    if (batchResults.length === 0) return;
    const csv = Papa.unparse(batchResults);
    const blob = new Blob([csv], { type: 'text/csv;charset=utf-8-sig;' }); // Added BOM for Excel Turkish chars
    const url = URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.setAttribute('download', 'batch_results.csv');
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
  };

  // Translations
  const t = {
    title: lang === 'tr' ? 'Destek Talebi Sınıflandırma' : 'Support Ticket Classification',
    desc: lang === 'tr' ? 'Yapay zeka ile müşteri taleplerinin kategorisini ve önceliğini otomatik belirleyin.' : 'Automatically predict category and priority of tickets using AI.',
    single: lang === 'tr' ? 'Tekli Analiz' : 'Single Analysis',
    batch: lang === 'tr' ? 'Toplu (Batch) Yükleme' : 'Batch Upload',
    placeholder: lang === 'tr' ? "Müşterinin mesajını buraya girin... (Örn: Dün aldığım ürünü iade etmek istiyorum.)" : "Enter customer message... (e.g., I want to return the product I bought yesterday.)",
    analyze: lang === 'tr' ? 'Yapay Zeka ile Analiz Et' : 'Analyze with AI',
    results: lang === 'tr' ? 'Analiz Sonuçları' : 'Analysis Results',
    uploadTitle: lang === 'tr' ? 'Yüklemek için tıklayın (.csv veya .txt)' : 'Click to upload (.csv or .txt)',
    download: lang === 'tr' ? 'CSV İndir' : 'Download CSV',
    processing: lang === 'tr' ? 'Talepler işleniyor...' : 'Processing tickets...',
    uploadAnother: lang === 'tr' ? 'Başka bir dosya yükle' : 'Upload another file',
    systemStatus: lang === 'tr' ? 'Sistem Durumu' : 'System Status',
    theme: lang === 'tr' ? 'Tema' : 'Theme',
    language: lang === 'tr' ? 'Dil' : 'Language',
    category: lang === 'tr' ? 'Kategori' : 'Category',
    priority: lang === 'tr' ? 'Öncelik' : 'Priority',
    confidence: lang === 'tr' ? 'Güven' : 'Confidence',
    text: lang === 'tr' ? 'Metin' : 'Text',
    records: lang === 'tr' ? 'kayıt işlendi' : 'records processed',
    apiOnline: lang === 'tr' ? 'API Aktif' : 'API Online',
    apiOffline: lang === 'tr' ? 'API Çevrimdışı' : 'API Offline',
    history: lang === 'tr' ? 'Geçmiş Analizler' : 'Recent Analyses',
    clearHistory: lang === 'tr' ? 'Geçmişi Temizle' : 'Clear History',
    systemManagement: lang === 'tr' ? 'Sistem Yönetimi' : 'System Management'
  };

  const translateVal = (val: string) => {
    if (lang === 'en') return val;
    const map: Record<string, string> = {
      'Account Management': 'Hesap Yönetimi',
      'Billing': 'Fatura ve Ödeme',
      'General Inquiry': 'Genel Soru',
      'Refund': 'İade',
      'Technical Issue': 'Teknik Sorun',
      'critical': 'Kritik',
      'high': 'Yüksek',
      'medium': 'Orta',
      'low': 'Düşük'
    };
    return map[val] || val;
  };

  const getPriorityStyles = (p: string, themeStr: string) => {
    if (!p) return { text: 'text-amber-500', bg: themeStr === 'dark' ? 'bg-amber-500/10' : 'bg-amber-50', border: 'border-amber-500/20' };
    const pLower = p.toLowerCase();
    if (pLower.includes('critical') || pLower.includes('kritik')) return { text: 'text-red-500', bg: themeStr === 'dark' ? 'bg-red-500/10' : 'bg-red-50', border: 'border-red-500/20' };
    if (pLower.includes('high') || pLower.includes('yüksek')) return { text: 'text-orange-500', bg: themeStr === 'dark' ? 'bg-orange-500/10' : 'bg-orange-50', border: 'border-orange-500/20' };
    if (pLower.includes('medium') || pLower.includes('orta')) return { text: 'text-blue-500', bg: themeStr === 'dark' ? 'bg-blue-500/10' : 'bg-blue-50', border: 'border-blue-500/20' };
    if (pLower.includes('low') || pLower.includes('düşük')) return { text: 'text-slate-500', bg: themeStr === 'dark' ? 'bg-slate-500/10' : 'bg-slate-50', border: 'border-slate-500/20' };
    return { text: 'text-amber-500', bg: themeStr === 'dark' ? 'bg-amber-500/10' : 'bg-amber-50', border: 'border-amber-500/20' };
  };

  // Theming classes
  const bgMain = theme === 'dark' ? 'bg-slate-900 text-slate-100' : 'bg-slate-50 text-slate-800';
  const bgCard = theme === 'dark' ? 'bg-slate-800 border-slate-700' : 'bg-white border-slate-200';
  const textMuted = theme === 'dark' ? 'text-slate-400' : 'text-slate-500';
  const bgSidebar = theme === 'dark' ? 'bg-slate-900 border-slate-800' : 'bg-white border-slate-200';
  const inputBg = theme === 'dark' ? 'bg-slate-900 border-slate-700 text-slate-100' : 'bg-slate-50 border-slate-200 text-slate-700';

  return (
    <div className={`min-h-screen font-sans flex transition-colors ${bgMain}`}>
      {/* Sidebar - Sticky & Collapsible */}
      <div className={`sticky top-0 h-screen flex-shrink-0 transition-all duration-300 border-r shadow-sm z-20 flex flex-col ${bgSidebar} ${sidebarOpen ? 'w-72 p-6' : 'w-20 p-4 items-center'}`}>
        <div className={`flex items-center text-indigo-500 font-bold text-xl mb-8 ${sidebarOpen ? 'gap-3' : 'justify-center'}`}>
          <Activity className="w-6 h-6 flex-shrink-0" />
          {sidebarOpen && <span>Ticket AI</span>}
        </div>
        
        {sidebarOpen ? (
          <div className="mb-6">
            <h3 className={`text-xs font-semibold uppercase tracking-wider mb-3 flex items-center gap-2 ${textMuted}`}>
              <Settings className="w-4 h-4" /> {t.systemStatus}
            </h3>
            <div className={`flex items-center gap-2 text-sm px-3 py-2 rounded-md ${health === 'ok' ? 'bg-emerald-500/10 text-emerald-600' : 'bg-red-500/10 text-red-600'}`}>
              {health === 'ok' ? <CheckCircle className="w-4 h-4 flex-shrink-0" /> : <AlertCircle className="w-4 h-4 flex-shrink-0" />}
              <span>{health === 'ok' ? t.apiOnline : t.apiOffline}</span>
            </div>
          </div>
        ) : (
          <div className={`p-2 rounded-full ${health === 'ok' ? 'text-emerald-500 bg-emerald-500/10' : 'text-red-500 bg-red-500/10'} mb-6`} title={health === 'ok' ? t.apiOnline : t.apiOffline}>
            {health === 'ok' ? <CheckCircle className="w-5 h-5" /> : <AlertCircle className="w-5 h-5" />}
          </div>
        )}

        {/* System Management Links */}
        {sidebarOpen ? (
          <div className="mb-8">
            <h3 className={`text-xs font-semibold uppercase tracking-wider mb-3 flex items-center gap-2 ${textMuted}`}>
              <Server className="w-4 h-4" /> {t.systemManagement}
            </h3>
            <div className="space-y-1">
              <button onClick={() => handleStartService('mlflow', 'http://localhost:5000')} className={`w-full flex items-center justify-between px-3 py-2 rounded-md text-sm transition-colors cursor-pointer hover:bg-slate-500/10 ${theme === 'dark' ? 'text-slate-300' : 'text-slate-700'}`}>
                <div className="flex items-center gap-2"><Beaker className="w-4 h-4 text-blue-500" /> MLflow</div>
                <ExternalLink className="w-3 h-3 opacity-50" />
              </button>
              <button onClick={() => handleStartService('prometheus', 'http://localhost:9090')} className={`w-full flex items-center justify-between px-3 py-2 rounded-md text-sm transition-colors cursor-pointer hover:bg-slate-500/10 ${theme === 'dark' ? 'text-slate-300' : 'text-slate-700'}`}>
                <div className="flex items-center gap-2"><Activity className="w-4 h-4 text-orange-500" /> Prometheus</div>
                <ExternalLink className="w-3 h-3 opacity-50" />
              </button>
              <button onClick={() => handleStartService('grafana', 'http://localhost:3000')} className={`w-full flex items-center justify-between px-3 py-2 rounded-md text-sm transition-colors cursor-pointer hover:bg-slate-500/10 ${theme === 'dark' ? 'text-slate-300' : 'text-slate-700'}`}>
                <div className="flex items-center gap-2"><LayoutDashboard className="w-4 h-4 text-amber-500" /> Grafana</div>
                <ExternalLink className="w-3 h-3 opacity-50" />
              </button>
              <button onClick={() => handleStartService('kubernetes', 'http://localhost:8001/api/v1/namespaces/kubernetes-dashboard/services/http:kubernetes-dashboard:/proxy/')} className={`w-full flex items-center justify-between px-3 py-2 rounded-md text-sm transition-colors cursor-pointer hover:bg-slate-500/10 ${theme === 'dark' ? 'text-slate-300' : 'text-slate-700'}`}>
                <div className="flex items-center gap-2"><Box className="w-4 h-4 text-indigo-500" /> Kubernetes</div>
                <ExternalLink className="w-3 h-3 opacity-50" />
              </button>
            </div>
          </div>
        ) : (
          <div className="flex flex-col gap-4 items-center mb-8 w-full border-t border-b border-slate-500/10 py-4">
            <button onClick={() => handleStartService('mlflow', 'http://localhost:5000')} className="p-2 rounded-md cursor-pointer hover:bg-slate-500/10" title="MLflow">
              <Beaker className="w-5 h-5 text-blue-500" />
            </button>
            <button onClick={() => handleStartService('prometheus', 'http://localhost:9090')} className="p-2 rounded-md cursor-pointer hover:bg-slate-500/10" title="Prometheus">
              <Activity className="w-5 h-5 text-orange-500" />
            </button>
            <button onClick={() => handleStartService('grafana', 'http://localhost:3000')} className="p-2 rounded-md cursor-pointer hover:bg-slate-500/10" title="Grafana">
              <LayoutDashboard className="w-5 h-5 text-amber-500" />
            </button>
            <button onClick={() => handleStartService('kubernetes', 'http://localhost:8001/api/v1/namespaces/kubernetes-dashboard/services/http:kubernetes-dashboard:/proxy/')} className="p-2 rounded-md cursor-pointer hover:bg-slate-500/10" title="Kubernetes">
              <Box className="w-5 h-5 text-indigo-500" />
            </button>
          </div>
        )}

        <div className="mt-auto space-y-4 w-full">
          {sidebarOpen ? (
            <>
              <div className="flex items-center justify-between">
                <span className={`text-sm font-medium ${textMuted}`}>{t.theme}</span>
                <button onClick={() => setTheme(th => th === 'light' ? 'dark' : 'light')} className="p-2 rounded-lg bg-slate-500/10 hover:bg-slate-500/20 transition-colors cursor-pointer">
                  {theme === 'light' ? <Moon className="w-4 h-4" /> : <Sun className="w-4 h-4" />}
                </button>
              </div>
              <div className="flex items-center justify-between">
                <span className={`text-sm font-medium ${textMuted}`}>{t.language}</span>
                <button onClick={() => setLang(l => l === 'tr' ? 'en' : 'tr')} className="px-3 py-1.5 rounded-lg bg-slate-500/10 hover:bg-slate-500/20 transition-colors cursor-pointer flex items-center gap-2 text-sm font-bold tracking-wide">
                  <Globe className="w-4 h-4" /> {lang.toUpperCase()}
                </button>
              </div>
            </>
          ) : (
            <div className="flex flex-col gap-4 items-center">
              <button onClick={() => setTheme(th => th === 'light' ? 'dark' : 'light')} className="p-3 rounded-full bg-slate-500/10 hover:bg-slate-500/20 transition-colors cursor-pointer" title={t.theme}>
                {theme === 'light' ? <Moon className="w-5 h-5" /> : <Sun className="w-5 h-5" />}
              </button>
              <button onClick={() => setLang(l => l === 'tr' ? 'en' : 'tr')} className="p-3 rounded-full bg-slate-500/10 hover:bg-slate-500/20 transition-colors cursor-pointer text-xs font-bold" title={t.language}>
                {lang.toUpperCase()}
              </button>
            </div>
          )}
        </div>
      </div>
      
      {/* Sidebar Toggle Button (floating next to sidebar) */}
      <button 
        onClick={() => setSidebarOpen(!sidebarOpen)} 
        className={`fixed left-0 top-6 z-30 p-1.5 rounded-r-lg bg-indigo-500 text-white shadow-md hover:bg-indigo-600 transition-all cursor-pointer ${sidebarOpen ? 'translate-x-72' : 'translate-x-20'}`}
      >
        {sidebarOpen ? <ChevronLeft className="w-4 h-4" /> : <ChevronRight className="w-4 h-4" />}
      </button>

      {/* Main Content */}
      <div className="flex-1 flex flex-col py-10 px-6 sm:px-10">
        <div className="w-full max-w-[1400px] mx-auto">
          <header className="mb-8">
            <h1 className="text-3xl font-extrabold mb-2 tracking-tight">{t.title}</h1>
            <p className={textMuted}>{t.desc}</p>
          </header>

          <div className={`rounded-2xl shadow-sm border overflow-hidden mb-8 transition-colors ${bgCard}`}>
            <div className="flex border-b border-slate-500/10">
              <button 
                onClick={() => setActiveTab('single')}
                className={`flex-1 py-4 text-sm font-medium transition-colors cursor-pointer ${activeTab === 'single' ? 'text-indigo-500 border-b-2 border-indigo-500' : `${textMuted} hover:text-indigo-400`}`}
              >
                {t.single}
              </button>
              <button 
                onClick={() => setActiveTab('batch')}
                className={`flex-1 py-4 text-sm font-medium transition-colors cursor-pointer ${activeTab === 'batch' ? 'text-indigo-500 border-b-2 border-indigo-500' : `${textMuted} hover:text-indigo-400`}`}
              >
                {t.batch}
              </button>
              <button 
                onClick={() => setActiveTab('history')}
                className={`flex-1 py-4 text-sm font-medium transition-colors cursor-pointer ${activeTab === 'history' ? 'text-indigo-500 border-b-2 border-indigo-500' : `${textMuted} hover:text-indigo-400`}`}
              >
                {t.history}
              </button>
            </div>

            <div className="p-8">
              {activeTab === 'single' && (
                <div className="space-y-4">
                  <textarea
                    value={text}
                    onChange={(e) => setText(e.target.value)}
                    placeholder={t.placeholder}
                    className={`w-full h-40 p-4 border rounded-xl focus:ring-2 focus:ring-indigo-500 outline-none resize-none transition-colors ${inputBg}`}
                  />
                  {error && (
                    <div className="flex items-center gap-2 text-sm text-red-600 bg-red-500/10 p-3 rounded-lg border border-red-500/20">
                      <AlertTriangle className="w-5 h-5 flex-shrink-0" /> {error}
                    </div>
                  )}
                  <div className="flex justify-end">
                    <button
                      onClick={handleAnalyze}
                      disabled={loading}
                      className={`cursor-pointer bg-indigo-600 hover:bg-indigo-700 text-white px-6 py-3 rounded-xl font-medium flex items-center gap-2 ${loading ? 'opacity-70 pointer-events-none' : ''}`}
                    >
                      {loading ? <div className="w-5 h-5 border-2 border-t-transparent rounded-full animate-spin" /> : <Send className="w-4 h-4" />}
                      {t.analyze}
                    </button>
                  </div>

                  {result && (
                    <div className="flex flex-col w-full">
                    {result.explainability && (
                      <div className="mt-6 pt-4 border-t border-slate-500/20">
                        <h4 className="text-sm font-semibold mb-3 flex items-center gap-2">
                          <Zap className="w-4 h-4 text-purple-400" /> 
                          {lang === 'tr' ? 'Model Açıklanabilirliği (SHAP / LIME)' : 'Model Explainability (SHAP / LIME)'}
                        </h4>
                        <div className="flex flex-wrap gap-2">
                          {Object.entries(result.explainability).map(([word, score]) => (
                            <div key={word} className={`flex items-center gap-2 px-3 py-1 rounded-full text-xs font-medium ${theme === 'dark' ? 'bg-slate-700 text-white' : 'bg-slate-200 text-slate-800'}`}>
                              <span>{word}</span>
                              <span className={`opacity-80 px-1.5 py-0.5 rounded text-[10px] ${
                                (score as number) > 0.7 ? 'bg-red-500/20 text-red-500' :
                                (score as number) > 0.4 ? 'bg-orange-500/20 text-orange-500' :
                                'bg-blue-500/20 text-blue-500'
                              }`}>
                                {(score as number).toFixed(2)}
                              </span>
                            </div>
                          ))}
                        </div>
                      </div>
                    )}

                    <div className="mt-8 pt-8 border-t border-slate-500/10 grid grid-cols-1 md:grid-cols-3 gap-6">
                      <div className={`p-5 rounded-2xl border border-indigo-500/20 ${theme === 'dark' ? 'bg-indigo-500/10' : 'bg-indigo-50'}`}>
                        <p className="text-xs text-indigo-500 font-semibold uppercase mb-1">{t.category}</p>
                        <p className="text-xl font-bold text-indigo-500">{translateVal(result.category)}</p>
                      </div>
                      <div className={`p-5 rounded-2xl border ${getPriorityStyles(result.priority, theme).border} ${getPriorityStyles(result.priority, theme).bg}`}>
                        <p className={`text-xs font-semibold uppercase mb-1 ${getPriorityStyles(result.priority, theme).text}`}>{t.priority}</p>
                        <p className={`text-xl font-bold capitalize ${getPriorityStyles(result.priority, theme).text}`}>{translateVal(result.priority)}</p>
                      </div>
                      <div className={`p-5 rounded-2xl border border-emerald-500/20 ${theme === 'dark' ? 'bg-emerald-500/10' : 'bg-emerald-50'}`}>
                        <p className="text-xs text-emerald-500 font-semibold uppercase mb-1">{t.confidence}</p>
                        <p className="text-xl font-bold text-emerald-500">{(result.confidence * 100).toFixed(1)}%</p>
                      </div>
                    </div>
                    </div>
                  )}
                </div>
              )}

              {activeTab === 'batch' && (
                <div>
                  <input type="file" accept=".csv,.txt" ref={fileInputRef} className="hidden" onChange={processBatchFile} />
                  
                  {!isBatching && batchResults.length === 0 && (
                    <div 
                      onClick={() => fileInputRef.current?.click()}
                      className={`py-12 flex flex-col items-center border-2 border-dashed rounded-2xl cursor-pointer group transition-colors ${theme === 'dark' ? 'border-slate-700 hover:border-indigo-500 hover:bg-indigo-500/5' : 'border-slate-200 hover:border-indigo-300 hover:bg-indigo-50/50'}`}
                    >
                      <Upload className="w-10 h-10 text-slate-400 group-hover:text-indigo-500 mb-4" />
                      <p className="font-medium group-hover:text-indigo-500">{t.uploadTitle}</p>
                    </div>
                  )}

                  {isBatching && (
                    <div className="py-12 flex flex-col items-center">
                      <div className="w-12 h-12 border-4 border-indigo-500/20 border-t-indigo-500 rounded-full animate-spin mb-4" />
                      <p className="font-medium">{t.processing}</p>
                      <p className={`text-sm ${textMuted}`}>{batchProgress.current} / {batchProgress.total}</p>
                    </div>
                  )}

                  {batchResults.length > 0 && !isBatching && (
                    <div>
                      <div className="flex justify-between items-center mb-4">
                        <p className={`text-sm font-medium ${textMuted}`}>{batchResults.length} {t.records}</p>
                        <button onClick={downloadCSV} className="flex items-center gap-2 text-sm text-white bg-indigo-600 hover:bg-indigo-700 px-4 py-2 rounded-lg font-medium transition-colors cursor-pointer">
                          <Download className="w-4 h-4" /> {t.download}
                        </button>
                      </div>
                      
                      {/* TABLE */}
                      <div className={`overflow-x-auto border rounded-xl ${theme === 'dark' ? 'border-slate-700' : 'border-slate-200'}`}>
                        <table className="w-full text-sm text-left table-fixed">
                          <thead className={`text-xs uppercase ${theme === 'dark' ? 'bg-slate-900 text-slate-400 border-b border-slate-700' : 'bg-slate-50 text-slate-500 border-b border-slate-200'}`}>
                            <tr>
                              <th className="px-6 py-4 w-[55%]">{t.text}</th>
                              <th className="px-6 py-4 w-[15%]">{t.category}</th>
                              <th className="px-6 py-4 w-[15%]">{t.priority}</th>
                              <th className="px-6 py-4 w-[15%]">{t.confidence}</th>
                            </tr>
                          </thead>
                          <tbody className="divide-y divide-slate-500/10">
                            {batchResults.map((r, i) => {
                              return (
                                <tr key={i} className={theme === 'dark' ? 'hover:bg-slate-800/50' : 'hover:bg-slate-50'}>
                                  <td 
                                    className="px-6 py-4 cursor-pointer group"
                                    onClick={() => setModalData({ Text: r.Text, Category: r.Category, Priority: r.Priority, Confidence: r.Confidence })}
                                  >
                                    <div className={`text-sm truncate transition-colors ${theme === 'dark' ? 'group-hover:text-indigo-400' : 'group-hover:text-indigo-600'}`}>
                                      {r.Text}
                                    </div>
                                  </td>
                                  <td className={`px-6 py-4 font-medium truncate ${r.Category.includes('Hata') || r.Category.includes('Error') ? 'text-red-500' : 'text-indigo-500'}`}>{translateVal(r.Category)}</td>
                                  <td className={`px-6 py-4 truncate capitalize font-semibold ${getPriorityStyles(r.Priority, theme).text}`}>{translateVal(r.Priority)}</td>
                                  <td className="px-6 py-4 truncate">{r.Confidence}</td>
                                </tr>
                              );
                            })}
                          </tbody>
                        </table>
                      </div>
                      <button 
                        onClick={() => setBatchResults([])}
                        className={`mt-4 text-sm underline cursor-pointer ${textMuted} hover:text-indigo-500`}
                      >
                        {t.uploadAnother}
                      </button>
                    </div>
                  )}
                </div>
              )}

              {activeTab === 'history' && (
                <div>
                  <div className="flex items-center justify-between mb-4">
                    <p className={`text-sm font-medium ${textMuted}`}>{history.length} {t.records}</p>
                    {history.length > 0 && (
                      <button onClick={() => setHistory([])} className={`text-sm underline cursor-pointer text-red-500 hover:text-red-600`}>
                        {t.clearHistory}
                      </button>
                    )}
                  </div>

                  {history.length === 0 ? (
                    <div className={`py-12 text-center text-sm ${textMuted}`}>
                      {lang === 'tr' ? 'Henüz hiç analiz yapmadınız.' : 'No recent analyses.'}
                    </div>
                  ) : (
                    <div className={`overflow-x-auto border rounded-xl ${theme === 'dark' ? 'border-slate-700' : 'border-slate-200'}`}>
                      <table className="w-full text-sm text-left table-fixed">
                        <thead className={`text-xs uppercase ${theme === 'dark' ? 'bg-slate-900 text-slate-400 border-b border-slate-700' : 'bg-slate-50 text-slate-500 border-b border-slate-200'}`}>
                          <tr>
                            <th className="px-6 py-4 w-[50%]">{t.text}</th>
                            <th className="px-6 py-4 w-[15%]">{t.category}</th>
                            <th className="px-6 py-4 w-[15%]">{t.priority}</th>
                            <th className="px-6 py-4 w-[20%]">Tarih / Date</th>
                          </tr>
                        </thead>
                        <tbody className="divide-y divide-slate-500/10">
                          {history.map((h, i) => (
                            <tr key={i} className={theme === 'dark' ? 'hover:bg-slate-800/50' : 'hover:bg-slate-50'}>
                              <td 
                                className="px-6 py-4 cursor-pointer group"
                                onClick={() => setModalData({ Text: h.text, Category: h.category, Priority: h.priority, Confidence: `${(h.confidence * 100).toFixed(1)}%` })}
                              >
                                <div className={`text-sm truncate transition-colors ${theme === 'dark' ? 'group-hover:text-indigo-400' : 'group-hover:text-indigo-600'}`}>
                                  {h.text}
                                </div>
                              </td>
                              <td className="px-6 py-4 font-medium truncate text-indigo-500">{translateVal(h.category)}</td>
                              <td className={`px-6 py-4 truncate capitalize font-semibold ${getPriorityStyles(h.priority, theme).text}`}>{translateVal(h.priority)}</td>
                              <td className={`px-6 py-4 truncate text-xs ${textMuted}`}>
                                {new Date(h.date).toLocaleString(lang === 'tr' ? 'tr-TR' : 'en-US')}
                              </td>
                            </tr>
                          ))}
                        </tbody>
                      </table>
                    </div>
                  )}
                </div>
              )}
            </div>
          </div>
        </div>
      </div>

      {/* Modal for viewing full text */}
      {modalData && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-900/50 backdrop-blur-sm" onClick={() => setModalData(null)}>
          <div 
            className={`w-full max-w-2xl rounded-2xl shadow-xl overflow-hidden flex flex-col ${theme === 'dark' ? 'bg-slate-800 border border-slate-700' : 'bg-white'}`} 
            onClick={e => e.stopPropagation()}
          >
            <div className={`p-4 border-b flex justify-between items-center ${theme === 'dark' ? 'border-slate-700 bg-slate-800/50' : 'border-slate-100 bg-slate-50'}`}>
              <h3 className="font-bold text-lg">{t.text}</h3>
              <button onClick={() => setModalData(null)} className={`w-8 h-8 flex items-center justify-center rounded-full transition-colors cursor-pointer ${theme === 'dark' ? 'hover:bg-slate-700' : 'hover:bg-slate-200'}`}>
                ✕
              </button>
            </div>
            <div className="p-6 overflow-y-auto max-h-[60vh] custom-scrollbar">
              <p className={`text-base leading-relaxed whitespace-pre-wrap ${theme === 'dark' ? 'text-slate-300' : 'text-slate-700'}`}>
                {modalData.Text}
              </p>
            </div>
            
              {modalData.Explainability && (
                <div className={`p-6 border-t ${theme === 'dark' ? 'border-slate-700' : 'border-slate-200'}`}>
                  <h4 className="text-sm font-semibold mb-3 flex items-center gap-2">
                    <Zap className="w-4 h-4 text-purple-400" /> 
                    {lang === 'tr' ? 'Model Açıklanabilirliği (SHAP / LIME)' : 'Model Explainability (SHAP / LIME)'}
                  </h4>
                  <div className="flex flex-wrap gap-2">
                    {Object.entries(modalData.Explainability).map(([word, score]) => (
                      <div key={word} className={`flex items-center gap-2 px-3 py-1 rounded-full text-xs font-medium ${theme === 'dark' ? 'bg-slate-700 text-white' : 'bg-slate-200 text-slate-800'}`}>
                        <span>{word}</span>
                        <span className={`opacity-80 px-1.5 py-0.5 rounded text-[10px] ${
                          (score as number) > 0.7 ? 'bg-red-500/20 text-red-500' :
                          (score as number) > 0.4 ? 'bg-orange-500/20 text-orange-500' :
                          'bg-blue-500/20 text-blue-500'
                        }`}>
                          {(score as number).toFixed(2)}
                        </span>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              <div className={`grid grid-cols-3 divide-x ${theme === 'dark' ? 'divide-slate-700 border-slate-700 bg-slate-900/50' : 'divide-slate-200 border-slate-200 bg-slate-50'} border-t`}>
              <div className="p-4 text-center flex flex-col justify-center">
                <p className={`text-xs font-semibold uppercase mb-1 tracking-wider ${theme === 'dark' ? 'text-slate-400' : 'text-slate-500'}`}>{t.category}</p>
                <p className={`text-lg font-bold ${modalData.Category.includes('Hata') || modalData.Category.includes('Error') ? 'text-red-500' : 'text-indigo-500'}`}>{translateVal(modalData.Category)}</p>
              </div>
              <div className="p-4 text-center flex flex-col justify-center">
                <p className={`text-xs font-semibold uppercase mb-1 tracking-wider ${theme === 'dark' ? 'text-slate-400' : 'text-slate-500'}`}>{t.priority}</p>
                <p className={`text-lg font-bold capitalize ${getPriorityStyles(modalData.Priority, theme).text}`}>{translateVal(modalData.Priority)}</p>
              </div>
              <div className="p-4 text-center flex flex-col justify-center">
                <p className={`text-xs font-semibold uppercase mb-1 tracking-wider ${theme === 'dark' ? 'text-slate-400' : 'text-slate-500'}`}>{t.confidence}</p>
                <p className="text-lg font-bold text-emerald-500">{modalData.Confidence}</p>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

export default App;
