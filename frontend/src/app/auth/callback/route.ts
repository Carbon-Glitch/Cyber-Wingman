import { createSupabaseServerClient } from '@/lib/supabase/server';
import { NextResponse } from 'next/server';

/**
 * OAuth 和 Magic Link 的回调端点。
 * Supabase 会把 `code` 参数带到这个 URL，我们用它换取 Session Cookie。
 */
export async function GET(request: Request) {
    const { searchParams, origin } = new URL(request.url);
    const code = searchParams.get('code');
    const next = searchParams.get('next') ?? '/';

    if (code) {
        const supabase = await createSupabaseServerClient();
        const { error } = await supabase.auth.exchangeCodeForSession(code);

        if (!error) {
            return NextResponse.redirect(`${origin}${next}`);
        }
    }

    // 出错时跳转到登录页，并带 error 参数以便展示提示信息
    return NextResponse.redirect(`${origin}/login?error=auth_failed`);
}
