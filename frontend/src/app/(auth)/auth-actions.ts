'use server';

import { redirect } from 'next/navigation';
import { createSupabaseServerClient } from '@/lib/supabase/server';

function getURL(path: string) {
    const baseUrl = process.env.NEXT_PUBLIC_SITE_URL ?? 'http://localhost:3000';
    return `${baseUrl.replace(/\/$/, '')}${path}`;
}

export async function signInWithOAuth(provider: 'github' | 'google') {
    const supabase = await createSupabaseServerClient();

    const { data, error } = await supabase.auth.signInWithOAuth({
        provider,
        options: {
            redirectTo: getURL('/auth/callback'),
        },
    });

    if (error) {
        console.error(error);
        return { data: null, error: error.message };
    }

    return redirect(data.url);
}

export async function signInWithEmail(email: string) {
    const supabase = await createSupabaseServerClient();

    const { error } = await supabase.auth.signInWithOtp({
        email,
        options: {
            emailRedirectTo: getURL('/auth/callback'),
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
