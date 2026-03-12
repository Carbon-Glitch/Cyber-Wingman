import { NextResponse } from 'next/server';

export async function POST(req: Request) {
    try {
        const { messages, quadrantId, userId, chatId, media } = await req.json();

        // The user's latest message is the last one in the messages array
        const latestMessage = messages[messages.length - 1]?.content || '';

        // Prepare payload for FastAPI backend
        const payload = {
            user_id: userId || 'test_user123',
            chat_id: chatId || 'test_chat123',
            message: latestMessage,
            quadrant: quadrantId || 'tactical',
            media: media || null,
        };

        // Forward the request to the FastAPI backend running at localhost:8000
        // Using SSE streaming
        const response = await fetch('http://127.0.0.1:8000/api/chat', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Accept': 'text/event-stream',
            },
            body: JSON.stringify(payload),
        });

        if (!response.ok) {
            const err = await response.text();
            return NextResponse.json({ error: `Backend error: ${err}` }, { status: response.status });
        }

        // Proxy the stream back to the client directly
        // The client will use a custom stream parser to handle the SSE
        return new Response(response.body, {
            headers: {
                'Content-Type': 'text/event-stream',
                'Cache-Control': 'no-cache',
                'Connection': 'keep-alive',
            }
        });

    } catch (error) {
        console.error('API Chat proxy error:', error);
        return NextResponse.json({ error: 'Failed to connect to backend' }, { status: 500 });
    }
}
