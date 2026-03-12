import { createServerClient } from '@supabase/ssr';
import { NextResponse, type NextRequest } from 'next/server';

/**
 * 在每次请求前刷新并维护 Supabase Session Cookie。
 * Chat-First 模式：不强制跳转登录，登录拦截由前端组件负责。
 *
 * 安全守衛：若環境變數未設定（如 Vercel 尚未配置），直接 pass-through，
 * 避免 Edge Runtime 崩潰導致 MIDDLEWARE_INVOCATION_FAILED。
 */
export async function updateSession(request: NextRequest) {
    // ── 環境變數守衛 ─────────────────────────────────────────────
    const supabaseUrl = process.env.NEXT_PUBLIC_SUPABASE_URL;
    const supabaseAnonKey = process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY;

    if (!supabaseUrl || !supabaseAnonKey) {
        // Supabase 未配置時直接放行，不崩潰
        console.warn('[middleware] Supabase env vars not set, skipping session refresh.');
        return NextResponse.next({ request });
    }

    let supabaseResponse = NextResponse.next({ request });

    const supabase = createServerClient(
        supabaseUrl,
        supabaseAnonKey,
        {
            cookies: {
                getAll() {
                    return request.cookies.getAll();
                },
                setAll(cookiesToSet) {
                    cookiesToSet.forEach(({ name, value }) =>
                        request.cookies.set(name, value)
                    );
                    supabaseResponse = NextResponse.next({ request });
                    cookiesToSet.forEach(({ name, value, options }) =>
                        supabaseResponse.cookies.set(name, value, options)
                    );
                },
            },
        }
    );

    // 刷新 session（维持登录状态），但不做任何重定向
    await supabase.auth.getUser();

    return supabaseResponse;
}
