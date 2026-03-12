import { createBrowserClient } from '@supabase/ssr';

/**
 * 用于 'use client' 组件的 Supabase Client。
 * 全局单例模式，避免重复创建。
 */
export function createSupabaseBrowserClient() {
    return createBrowserClient(
        process.env.NEXT_PUBLIC_SUPABASE_URL || 'https://placeholder.supabase.co',
        process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY || 'placeholder'
    );
}
