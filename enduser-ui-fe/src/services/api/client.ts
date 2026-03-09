import { createClient, SupabaseClient } from '@supabase/supabase-js';

const getSupabaseConfig = () => {
    // 1. Try Environment Variables first (Vite injection)
    let url = import.meta.env.VITE_SUPABASE_URL;
    let key = import.meta.env.VITE_SUPABASE_ANON_KEY;
    
    // 2. Fallback to localStorage (User override for Dev)
    if (!url || !key) {
        url = localStorage.getItem('supabaseUrl') || "";
        key = localStorage.getItem('supabaseAnonKey') || "";
    }

    // 🟢 RULE 7: Proactive Guard against Docker DNS pollution (_kong)
    if (url && url.includes('_kong')) {
        console.warn("⚠️ [Security] Internal Docker DNS detected in Frontend. Blocking request to prevent DNS hang.");
        return { url: null, key: null };
    }

    return { url: url || null, key: key || null };
};

const { url: supabaseUrl, key: supabaseAnonKey } = getSupabaseConfig();

export let supabase: SupabaseClient | null = null;

if (!supabaseUrl || !supabaseAnonKey || supabaseUrl === 'YOUR_SUPABASE_URL') {
    console.error("Supabase credentials are not set. API calls will fail.");
} else {
    try {
        supabase = createClient(supabaseUrl!, supabaseAnonKey!); 
    } catch (error) {
        console.error("Failed to initialize Supabase client:", error);
    }
}
