import { createServerClient } from '@supabase/ssr';
import { cookies } from 'next/headers';

/**
 * 用于 Server Components / Server Actions / Route Handlers 的 Supabase Client。
 * 自动从 Cookie 中读取用户 Session。
 */
export async function createSupabaseServerClient() {
    const cookieStore = await cookies();

    return createServerClient(
        process.env.NEXT_PUBLIC_SUPABASE_URL!,
        process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY!,
        {
            cookies: {
                getAll() {
                    return cookieStore.getAll();
                },
                setAll(cookiesToSet) {
                    try {
                        cookiesToSet.forEach(({ name, value, options }) =>
                            cookieStore.set(name, value, options)
                        );
                    } catch {
                        // 在 Server Component 中调用 setAll 会抛出，可安全忽略
                        // 真正的 Session 刷新由 middleware 负责
                    }
                },
            },
        }
    );
}
