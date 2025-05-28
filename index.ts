Bun.serve({
  routes: {
    "/": new Response("Hello via Bun!"),
  },
});