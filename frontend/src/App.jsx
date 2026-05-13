import React, { useState, useRef } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import jsPDF from 'jspdf';
import html2canvas from 'html2canvas';

function App() {
  const [url, setUrl] = useState('');
  const [loading, setLoading] = useState(false);
  const [recipe, setRecipe] = useState(null);
  const [error, setError] = useState('');
  const [copied, setCopied] = useState(false);
  const [view, setView] = useState('home'); // 'home' or 'cookbook'
  const [savedRecipes, setSavedRecipes] = useState(() => {
    const saved = localStorage.getItem('sous-chef-recipes');
    return saved ? JSON.parse(saved) : [];
  });
  const recipeRef = useRef(null);

  const saveRecipe = () => {
    if (!recipe) return;
    const isAlreadySaved = savedRecipes.some(r => r.title === recipe.title);
    if (isAlreadySaved) return;
    
    const updated = [recipe, ...savedRecipes];
    setSavedRecipes(updated);
    localStorage.setItem('sous-chef-recipes', JSON.stringify(updated));
    alert('Recipe saved to your cookbook!');
  };

  const removeRecipe = (index) => {
    const updated = savedRecipes.filter((_, i) => i !== index);
    setSavedRecipes(updated);
    localStorage.setItem('sous-chef-recipes', JSON.stringify(updated));
  };

  const handleExtract = async (e) => {
    if (e) e.preventDefault();
    if (!url) return;
    setLoading(true);
    setError('');
    setRecipe(null);
    const apiUrl = import.meta.env.VITE_API_URL || 'http://localhost:8000';
    
    try {
      const response = await fetch(`${apiUrl}/extract`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ url }),
      });
      if (!response.ok) throw new Error('Failed to extract recipe.');
      const data = await response.json();
      setRecipe(data);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const copyToClipboard = () => {
    const text = `${recipe.title}\n\nIngredients:\n${recipe.ingredients.join('\n')}\n\nInstructions:\n${recipe.instructions.join('\n')}`;
    navigator.clipboard.writeText(text);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  const downloadAsPDF = async () => {
    if (!recipeRef.current) return;
    const canvas = await html2canvas(recipeRef.current, { scale: 2, useCORS: true, backgroundColor: '#ffffff' });
    const imgData = canvas.toDataURL('image/png');
    const pdf = new jsPDF('p', 'mm', 'a4');
    const pdfWidth = pdf.internal.pageSize.getWidth();
    const pdfHeight = (canvas.height * pdfWidth) / canvas.width;
    pdf.addImage(imgData, 'PNG', 0, 0, pdfWidth, pdfHeight);
    pdf.save(`${recipe.title.replace(/\s+/g, '_')}_recipe.pdf`);
  };

  return (
    <div className="bg-[#fbf9f5] min-h-screen font-['Hanken_Grotesk'] text-[#1b1c1a] pb-24">
      {/* TopAppBar Navigation */}
      <header className="bg-[#fbf9f5] sticky top-0 z-50">
        <div className="flex justify-between items-center w-full px-5 md:px-16 py-4 max-w-[1200px] mx-auto">
          <div className="flex items-center gap-3 cursor-pointer" onClick={() => setView('home')}>
            <div className="w-14 h-14 rounded-xl overflow-hidden shadow-sm">
              <img 
                className="w-full h-full object-contain" 
                src="/logo.png" 
                alt="Sous Chef Logo"
              />
            </div>
            <h1 className="text-2xl font-bold text-[#7c5800]">Sous Chef</h1>
          </div>
          <div className="flex gap-4">
            <button 
              onClick={() => setView('home')}
              className={`px-4 py-2 rounded-xl text-sm font-bold transition-all ${view === 'home' ? 'bg-[#ffb800] text-white shadow-md' : 'hover:bg-[#f5f3ef]'}`}
            >
              Extract
            </button>
            <button 
              onClick={() => setView('cookbook')}
              className={`px-4 py-2 rounded-xl text-sm font-bold transition-all ${view === 'cookbook' ? 'bg-[#ffb800] text-white shadow-md' : 'hover:bg-[#f5f3ef]'}`}
            >
              My Cookbook ({savedRecipes.length})
            </button>
          </div>
        </div>
      </header>

      <main className="max-w-[1200px] mx-auto px-5 md:px-16 py-2 space-y-12">
        {view === 'home' ? (
          <>
            {/* Hero Section */}
            <section className="flex flex-col items-center text-center max-w-2xl mx-auto space-y-8 py-8">
              <div className="space-y-4">
                <h2 className="text-4xl md:text-5xl font-bold">Extract Recipe</h2>
                <p className="text-lg md:text-xl text-[#514532]">
                  Paste any recipe URL below to instantly strip away the clutter and save the core ingredients and instructions to your digital cookbook.
                </p>
              </div>

              <div className="w-full space-y-4">
                <form onSubmit={handleExtract} className="relative group">
                  <input 
                    className="w-full h-16 px-6 bg-white border-2 border-[#d5c4ab] rounded-2xl focus:outline-none focus:border-[#ffb800] text-lg transition-all shadow-sm" 
                    placeholder="https://your-favorite-recipe.com/..." 
                    type="url"
                    value={url}
                    onChange={(e) => setUrl(e.target.value)}
                    required
                  />
                  <button 
                    type="submit"
                    disabled={loading}
                    className="absolute right-3 top-3 h-10 px-6 bg-[#ffb800] text-white flex items-center justify-center font-bold rounded-xl cursor-pointer hover:bg-[#7c5800] transition-all active:scale-95 disabled:opacity-50 premium-button"
                  >
                    {loading ? <span className="material-symbols-outlined animate-spin">progress_activity</span> : 'Extract'}
                  </button>
                </form>
                <p className="text-xs text-[#837560] font-medium tracking-wide">Supports YouTube, Instagram & 500+ cooking blogs</p>
              </div>
            </section>

            {/* Dynamic Content: Results Only */}
            <AnimatePresence mode="wait">
              {loading && (
                <motion.div 
                  initial={{ opacity: 0 }}
                  animate={{ opacity: 1 }}
                  className="bg-white border border-[#d5c4ab] rounded-3xl p-8 md:p-12 space-y-12"
                >
                  <div className="flex flex-col md:flex-row gap-8">
                    <div className="w-full md:w-48 h-48 rounded-2xl skeleton" />
                    <div className="flex-grow space-y-4">
                      <div className="h-4 w-24 rounded bg-[#ffdea8] skeleton" />
                      <div className="h-10 w-3/4 rounded skeleton" />
                      <div className="flex gap-2">
                        <div className="h-10 w-24 rounded-xl skeleton" />
                        <div className="h-10 w-24 rounded-xl skeleton" />
                      </div>
                    </div>
                  </div>
                  <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                    {[1,2,3,4].map(i => <div key={i} className="h-20 rounded-2xl skeleton" />)}
                  </div>
                </motion.div>
              )}

              {recipe && !loading && (
                <motion.section 
                  key="recipe"
                  initial={{ opacity: 0, y: 20 }}
                  animate={{ opacity: 1, y: 0 }}
                  exit={{ opacity: 0, scale: 0.95 }}
                  ref={recipeRef}
                  className="bg-white border border-[#d5c4ab] rounded-3xl overflow-hidden shadow-lg p-8 md:p-12 space-y-12"
                >
                  <div className="flex flex-col md:flex-row gap-8 border-b border-[#d5c4ab]/20 pb-8">
                    {recipe.image && (
                      <div className="w-full md:w-48 h-32 md:h-48 rounded-2xl overflow-hidden flex-shrink-0 bg-[#fbf9f5] border border-[#d5c4ab]/30 shadow-sm">
                        <img src={recipe.image} alt={recipe.title} className="w-full h-full object-cover" />
                      </div>
                    )}
                    <div className="flex-grow flex flex-col justify-between gap-6">
                      <div className="space-y-2">
                        <span className="text-[10px] font-bold uppercase tracking-widest text-[#7c5800] bg-[#ffdea8] px-2 py-1 rounded">Generated Recipe</span>
                        <h3 className="text-3xl md:text-4xl font-bold leading-tight">{recipe.title}</h3>
                      </div>
                      <div className="flex flex-wrap gap-2">
                        <button onClick={copyToClipboard} className="flex items-center gap-2 px-4 py-2 bg-[#f5f3ef] hover:bg-[#e6ded9] rounded-xl text-sm font-bold transition-all premium-button">
                          <span className="material-symbols-outlined text-[20px]">{copied ? 'check_circle' : 'content_copy'}</span>
                          {copied ? 'Copied' : 'Copy'}
                        </button>
                        <button onClick={() => window.print()} className="flex items-center gap-2 px-4 py-2 bg-[#f5f3ef] hover:bg-[#e6ded9] rounded-xl text-sm font-bold transition-all premium-button">
                          <span className="material-symbols-outlined text-[20px]">print</span>
                          Print
                        </button>
                        <button 
                          onClick={saveRecipe}
                          className="flex items-center gap-2 px-4 py-2 bg-[#7c5800] text-white hover:bg-[#5e4200] rounded-xl text-sm font-bold transition-all premium-button"
                        >
                          <span className="material-symbols-outlined text-[20px]">bookmark</span>
                          Save to Cookbook
                        </button>
                      </div>
                    </div>
                  </div>

                  <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                    {[
                      { label: 'Prep Time', value: recipe.prep_time, icon: 'timer' },
                      { label: 'Cook Time', value: recipe.cook_time, icon: 'skillet' },
                      { label: 'Servings', value: recipe.servings, icon: 'group' },
                      { label: 'Difficulty', value: 'Medium', icon: 'star' }
                    ].map((stat, i) => (
                      <div key={i} className="p-4 bg-[#fbf9f5] border border-[#d5c4ab]/30 rounded-2xl flex flex-col items-center text-center gap-1">
                        <span className="material-symbols-outlined text-[#7c5800]">{stat.icon}</span>
                        <span className="text-[10px] uppercase font-bold text-[#837560] tracking-tighter">{stat.label}</span>
                        <span className="font-bold">{stat.value || 'N/A'}</span>
                      </div>
                    ))}
                  </div>

                  <div className="grid md:grid-cols-5 gap-12">
                    <div className="md:col-span-2 space-y-6">
                      <h4 className="text-xl font-bold flex items-center gap-2 text-[#7c5800]">
                        <span className="material-symbols-outlined">format_list_bulleted</span>
                        Ingredients
                      </h4>
                      <ul className="space-y-4">
                        {recipe.ingredients.map((item, i) => (
                          <li key={i} className="flex gap-3 text-sm md:text-base border-b border-[#d5c4ab]/10 pb-2">
                            <span className="text-[#ffb800] font-bold">•</span>
                            {item}
                          </li>
                        ))}
                      </ul>
                    </div>
                    <div className="md:col-span-3 space-y-6">
                      <h4 className="text-xl font-bold flex items-center gap-2 text-[#7c5800]">
                        <span className="material-symbols-outlined">auto_stories</span>
                        Instructions
                      </h4>
                      <div className="space-y-8">
                        {recipe.instructions.map((step, i) => (
                          <div key={i} className="flex gap-4">
                            <div className="w-6 h-6 flex-shrink-0 bg-[#7c5800] text-white rounded-full flex items-center justify-center text-[10px] font-bold">
                              {i + 1}
                            </div>
                            <p className="text-sm md:text-base leading-relaxed text-[#514532]">{step}</p>
                          </div>
                        ))}
                      </div>
                    </div>
                  </div>
                </motion.section>
              )}
            </AnimatePresence>
          </>
        ) : (
          <section className="space-y-12">
            <div className="flex justify-between items-end">
              <div className="space-y-2">
                <h2 className="text-4xl font-bold">My Cookbook</h2>
                <p className="text-[#514532]">You have {savedRecipes.length} recipes saved.</p>
              </div>
            </div>

            {savedRecipes.length === 0 ? (
              <div className="bg-white border border-[#d5c4ab] rounded-3xl p-20 text-center space-y-6">
                <span className="material-symbols-outlined text-6xl text-[#d5c4ab]">menu_book</span>
                <p className="text-xl text-[#837560]">Your cookbook is empty. Extract a recipe to get started!</p>
                <button 
                  onClick={() => setView('home')}
                  className="px-8 py-3 bg-[#7c5800] text-white rounded-xl font-bold premium-button"
                >
                  Go to Extractor
                </button>
              </div>
            ) : (
              <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-8">
                {savedRecipes.map((r, i) => (
                  <motion.div 
                    key={i}
                    layout
                    initial={{ opacity: 0, scale: 0.9 }}
                    animate={{ opacity: 1, scale: 1 }}
                    className="bg-white border border-[#d5c4ab] rounded-3xl overflow-hidden shadow-sm hover:shadow-md transition-shadow group"
                  >
                    <div className="h-48 overflow-hidden relative">
                      <img src={r.image || '/placeholder.jpg'} alt={r.title} className="w-full h-full object-cover group-hover:scale-105 transition-transform duration-500" />
                      <button 
                        onClick={() => removeRecipe(i)}
                        className="absolute top-4 right-4 w-10 h-10 bg-white/80 backdrop-blur rounded-full flex items-center justify-center text-red-500 hover:bg-white transition-colors"
                      >
                        <span className="material-symbols-outlined">delete</span>
                      </button>
                    </div>
                    <div className="p-6 space-y-4">
                      <h4 className="text-xl font-bold line-clamp-2 min-h-[3.5rem]">{r.title}</h4>
                      <div className="flex justify-between items-center text-xs text-[#837560] font-bold uppercase tracking-wider">
                        <span>{r.cook_time || 'N/A'}</span>
                        <button 
                          onClick={() => { setRecipe(r); setView('home'); }}
                          className="text-[#7c5800] hover:underline"
                        >
                          View Details
                        </button>
                      </div>
                    </div>
                  </motion.div>
                ))}
              </div>
            )}
          </section>
        )}
      </main>
    </div>
  );
}

export default App;
