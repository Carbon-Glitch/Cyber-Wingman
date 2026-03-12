'use server';

import { redirect } from 'next/navigation';
import { createSupabaseServerClient } from '@/lib/supabase/server';
import { headers } from 'next/headers';

async function getURL(path: string) {
    let baseUrl = process.env.NEXT_PUBLIC_SITE_URL ?? '';
    if (!baseUrl) {
        const headersList = await headers();
        const host = headersList.get('host') || 'localhost:3000';
        baseUrl = host.includes('localhost') ? `http://${host}` : `https://${host}`;
    }
    return `${baseUrl.replace(/\/$/, '')}${path}`;
}

export async function signInWithOAuth(provider: 'github' | 'google') {
    const supabase = await createSupabaseServerClient();
    const redirectToUrl = await getURL('/auth/callback');

    const { data, error } = await supabase.auth.signInWithOAuth({
        provider,
        options: {
            redirectTo: redirectToUrl,
        },
    });

    if (error) {
        console.error("signInWithOAuth error:", error);
        return { data: null, error: error.message };
    }

    return { data: { url: data.url }, error: null };
}

export async function signInWithEmail(email: string) {
    const supabase = await createSupabaseServerClient();

    const redirectToUrl = await getURL('/auth/callback');

    const { error } = await supabase.auth.signInWithOtp({
        email,
        options: {
            emailRedirectTo: redirectToUrl,
        },
    });

    if (error) {
        console.error(error);
        return { data: null, error: error.message };
    }

    return { data: null, error: null };
}

export async function signOut() {
    const supabase = await createSupabaseServerClient();
    const { error } = await supabase.auth.signOut();

    if (error) {
        console.error(error);
        return { data: null, error: error.message };
    }

    redirect('/login');
}
