import { useState, useEffect, useMemo, useCallback } from 'react';
import { api } from '../../../services/api.ts';
import { DocumentVersion, BlogPost } from '../../../types.ts';

// Hook for Document Versions
export const useDocumentVersions = () => {
    const [versions, setVersions] = useState<DocumentVersion[]>([]);
    const [searchTerm, setSearchTerm] = useState('');
    const [loading, setLoading] = useState(true);

    const fetchVersions = useCallback(() => {
        setLoading(true);
        api.getDocumentVersions()
            .then(setVersions)
            .catch(err => alert(`Failed to load document versions: ${err.message}`))
            .finally(() => setLoading(false));
    }, []);

    useEffect(() => {
        fetchVersions();
    }, [fetchVersions]);

    // PERFORMANCE: Precalculate lowercase searchable strings to prevent O(N) string allocations during typing.
    // Memoized to only recalculate when the original versions array changes.
    const searchableVersions = useMemo(() => {
        return versions.map(v =>
            `${v.created_by || ''} ${v.field_name || ''} ${v.change_summary || ''} ${v.change_type || ''}`.toLowerCase()
        );
    }, [versions]);

    const filteredVersions = useMemo(() => {
        const query = searchTerm.toLowerCase().trim();
        if (!query) return versions;
        return versions.filter((_, i) => searchableVersions[i].includes(query));
    }, [versions, searchTerm, searchableVersions]);

    return { versions, filteredVersions, searchTerm, setSearchTerm, loading, fetchVersions };
};

// Hook for Blog Posts
export const useBlogPosts = () => {
    const [posts, setPosts] = useState<BlogPost[]>([]);
    const [loading, setLoading] = useState(true);

    const fetchPosts = useCallback(() => {
        setLoading(true);
        api.getBlogPosts()
           .then(setPosts)
           .catch(err => alert(`Failed to load blog posts: ${err.message}`))
           .finally(() => setLoading(false));
    }, []);

    useEffect(() => {
        fetchPosts();
    }, [fetchPosts]);

    const deletePost = async (postId: string) => {
        if (!window.confirm('Are you sure you want to delete this post?')) return;
        try {
            await api.deleteBlogPost(postId);
            setPosts(prev => prev.filter(p => p.id !== postId));
            alert('Post deleted successfully!');
        } catch (error: any) {
            alert(`Failed to delete post: ${error.message}`);
        }
    };

    return { posts, loading, deletePost, fetchPosts };
};

// Hook for System Settings
export const useSystemSettings = (categories: string[]) => {
    const [settings, setSettings] = useState<any[]>([]);
    const [loading, setLoading] = useState(true);
    const [isSaving, setIsSaving] = useState<string | null>(null);

    const fetchSettings = useCallback(async () => {
        setLoading(true);
        try {
            const promises = categories.map(category => api.getSystemSettings(category));
            const results = await Promise.all(promises);
            const allSettings = results.flat();
            setSettings(allSettings);
        } catch (err: any) {
            alert("Failed to load settings: " + err.message);
        } finally {
            setLoading(false);
        }
    }, [categories.join(',')]); // eslint-disable-line react-hooks/exhaustive-deps

    useEffect(() => {
        fetchSettings();
    }, [fetchSettings]);

    const updateSetting = async (key: string, newValue: string) => {
        setIsSaving(key);
        try {
            await api.updateSystemSetting(key, { value: newValue });
            setSettings(prev => prev.map(s => s.key === key ? { ...s, value: newValue } : s));
        } catch (err: any) {
            alert("Update failed: " + err.message);
        } finally {
            setIsSaving(null);
        }
    };

    return { settings, loading, isSaving, updateSetting, fetchSettings };
};

// Hook for Extraction Schemas
export const useExtractionSchemas = () => {
    const [schemas, setSchemas] = useState<any[]>([]);
    const [loading, setLoading] = useState(true);
    const [analyzeUrl, setAnalyzeUrl] = useState('');
    const [isAnalyzing, setIsAnalyzing] = useState(false);
    const [suggestions, setSuggestions] = useState<any>(null);
    const [newSchemaName, setNewSchemaName] = useState('');
    const [newDomainPattern, setNewDomainPattern] = useState('');

    const fetchSchemas = useCallback(async () => {
        setLoading(true);
        try {
            const data = await api.getExtractionSchemas();
            setSchemas(data);
        } catch (err: any) {
            alert("Failed to load schemas: " + err.message);
        } finally {
            setLoading(false);
        }
    }, []);

    useEffect(() => {
        fetchSchemas();
    }, [fetchSchemas]);

    const analyzeStructure = async () => {
        if (!analyzeUrl) return;
        setIsAnalyzing(true);
        setSuggestions(null);
        try {
            // Ensure analyzeUrl has a protocol for the frontend URL parser
            const safeUrl = analyzeUrl.startsWith('http') ? analyzeUrl : `https://${analyzeUrl}`;
            const result = await api.analyzeExtractionUrl(safeUrl);
            setSuggestions(result);
            const url = new URL(safeUrl);
            setNewDomainPattern(`${url.hostname}${url.pathname.split('/').slice(0, 3).join('/')}/*`);
        } catch (err: any) {
            alert("Analysis failed: " + err.message);
        } finally {
            setIsAnalyzing(false);
        }
    };

    const saveSchema = async () => {
        if (!newSchemaName || !newDomainPattern || !suggestions) return;
        try {
            await api.createExtractionSchema({
                name: newSchemaName,
                domain_pattern: newDomainPattern,
                schema_definition: suggestions,
                description: `Auto-generated for ${newDomainPattern}`
            });
            alert("Schema saved successfully!");
            fetchSchemas();
            setSuggestions(null);
            setAnalyzeUrl('');
        } catch (err: any) {
            alert("Save failed: " + err.message);
        }
    };

    const deleteSchema = async (id: string) => {
        if (!window.confirm("Delete this extraction template?")) return;
        try {
            await api.deleteExtractionSchema(id);
            fetchSchemas();
        } catch (err: any) {
            alert("Delete failed: " + err.message);
        }
    };

    const runExtraction = async (schemaId: string) => {
        const url = prompt("Enter target URL to extract data from:");
        if (!url) return;
        try {
            const res = await api.runExtraction(url, schemaId);
            alert(res.message);
        } catch (err: any) {
            alert("Execution failed: " + err.message);
        }
    };

    return { 
        schemas, loading, analyzeUrl, setAnalyzeUrl, isAnalyzing, suggestions, 
        newSchemaName, setNewSchemaName, newDomainPattern, setNewDomainPattern,
        analyzeStructure, saveSchema, deleteSchema, runExtraction, fetchSchemas
    };
};

// Hook for Crawler Targets
export const useCrawlerTargets = () => {
    const [targets, setTargets] = useState<any[]>([]);
    const [loading, setLoading] = useState(true);
    const [newUrl, setNewUrl] = useState('');
    const [newDepth, setNewDepth] = useState(2);
    const [newDesc, setNewDesc] = useState('');
    const [isSaving, setIsSaving] = useState(false);

    const fetchTargets = useCallback(async () => {
        setLoading(true);
        try {
            const data = await api.getCrawlerTargets();
            setTargets(data);
        } catch (err: any) {
            console.error("Failed to load targets:", err);
        } finally {
            setLoading(false);
        }
    }, []);

    useEffect(() => {
        fetchTargets();
    }, [fetchTargets]);

    const saveTarget = async () => {
        if (!newUrl) return;
        setIsSaving(true);
        try {
            await api.createCrawlerTarget({
                target_url: newUrl,
                max_depth: newDepth,
                description: newDesc
            });
            setNewUrl('');
            setNewDesc('');
            setNewDepth(2);
            fetchTargets();
        } catch (err: any) {
            alert("Save failed: " + err.message);
        } finally {
            setIsSaving(false);
        }
    };

    const deleteTarget = async (id: string) => {
        if (!window.confirm("Delete this crawler target? Tasks relying on it may fail.")) return;
        try {
            await api.deleteCrawlerTarget(id);
            fetchTargets();
        } catch (err: any) {
            alert("Delete failed: " + err.message);
        }
    };

    return { 
        targets, loading, newUrl, setNewUrl, newDepth, setNewDepth, newDesc, setNewDesc, 
        isSaving, saveTarget, deleteTarget, fetchTargets 
    };
};
