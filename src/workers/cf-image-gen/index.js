/**
 * Cloudflare Workers AI Image Generation Endpoint
 * Model: @cf/black-forest-labs/flux-1-schnell (optimal free tier)
 * Endpoint: POST /generate
 * 
 * Deploy: npx wrangler deploy
 * Test: curl -X POST https://your-worker.workers.dev/generate -H "Content-Type: application/json" -d '{"prompt":"test"}'
 */

export default {
  async fetch(request, env) {
    const url = new URL(request.url);
    
    // CORS headers
    const corsHeaders = {
      "Access-Control-Allow-Origin": "*",
      "Access-Control-Allow-Methods": "POST, OPTIONS",
      "Access-Control-Allow-Headers": "Content-Type",
    };

    // Handle preflight
    if (request.method === "OPTIONS") {
      return new Response(null, { headers: corsHeaders });
    }

    // Health check
    if (url.pathname === "/health") {
      return new Response(JSON.stringify({ status: "ok", model: "@cf/black-forest-labs/flux-1-schnell" }), {
        headers: { ...corsHeaders, "Content-Type": "application/json" }
      });
    }

    // Generate endpoint
    if (url.pathname === "/generate" && request.method === "POST") {
      try {
        const { prompt, width = 1024, height = 1024, steps = 4, guidance_scale = 3.5 } = await request.json();

        if (!prompt || typeof prompt !== "string") {
          return new Response(JSON.stringify({ error: "prompt required (string)" }), {
            status: 400,
            headers: { ...corsHeaders, "Content-Type": "application/json" }
          });
        }

        // Safety suffix untuk news content
        const safetySuffix = ", abstract symbolic illustration, no realistic human faces, no specific real people, editorial illustration style, news infographic background";
        const safePrompt = `${prompt}${safetySuffix}`;

        // Call Workers AI
        const response = await env.AI.run("@cf/black-forest-labs/flux-1-schnell", {
          prompt: safePrompt,
          width: Math.min(Math.max(width, 512), 1024),
          height: Math.min(Math.max(height, 512), 1024),
          num_inference_steps: Math.min(Math.max(steps, 1), 8),
          guidance_scale: Math.min(Math.max(guidance_scale, 1), 10),
        });

        // Response from Workers AI for image models is a ReadableStream or ArrayBuffer
        // Convert to proper Response with binary data
        let imageData;
        if (response instanceof ReadableStream) {
          // Collect stream to ArrayBuffer
          const reader = response.getReader();
          const chunks = [];
          let done = false;
          while (!done) {
            const { value, done: streamDone } = await reader.read();
            done = streamDone;
            if (value) chunks.push(value);
          }
          // Concatenate chunks
          const totalLength = chunks.reduce((acc, chunk) => acc + chunk.length, 0);
          imageData = new Uint8Array(totalLength);
          let offset = 0;
          for (const chunk of chunks) {
            imageData.set(chunk, offset);
            offset += chunk.length;
          }
          imageData = imageData.buffer;
        } else if (response instanceof ArrayBuffer) {
          imageData = response;
        } else if (response && typeof response === 'object' && response.image) {
          // Some models return { image: base64String }
          const base64 = response.image;
          const binaryString = atob(base64);
          const bytes = new Uint8Array(binaryString.length);
          for (let i = 0; i < binaryString.length; i++) {
            bytes[i] = binaryString.charCodeAt(i);
          }
          imageData = bytes.buffer;
        } else {
          // Try to convert whatever we got
          imageData = new Response(response).arrayBuffer();
          imageData = await imageData;
        }

        return new Response(imageData, {
          headers: {
            ...corsHeaders,
            "Content-Type": "image/jpeg",
            "Cache-Control": "public, max-age=3600"
          }
        });

      } catch (error) {
        console.error("Generation error:", error);
        
        // Check if quota exceeded
        const errorMsg = error.message || String(error);
        const isQuotaError = errorMsg.includes("quota") || 
                            errorMsg.includes("limit") || 
                            errorMsg.includes("neurons") ||
                            errorMsg.includes("rate limit") ||
                            errorMsg.includes("429");
        
        return new Response(JSON.stringify({ 
          error: "generation_failed",
          message: errorMsg,
          quota_exceeded: isQuotaError
        }), {
          status: isQuotaError ? 429 : 500,
          headers: { ...corsHeaders, "Content-Type": "application/json" }
        });
      }
    }

    return new Response(JSON.stringify({ 
      error: "not_found", 
      endpoints: { generate: "POST /generate", health: "GET /health" }
    }), {
      status: 404,
      headers: { ...corsHeaders, "Content-Type": "application/json" }
    });
  }
};