export const DEFAULT_BLOG_COVER_IMAGE =
  "data:image/svg+xml;utf8," +
  encodeURIComponent(
    '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 800 420">' +
      '<defs><linearGradient id="g" x1="0" y1="0" x2="1" y2="1">' +
      '<stop offset="0%" stop-color="#1e1b4b"/><stop offset="50%" stop-color="#312e81"/><stop offset="100%" stop-color="#0f172a"/>' +
      "</linearGradient></defs>" +
      '<rect width="800" height="420" fill="url(#g)"/>' +
      '<circle cx="650" cy="90" r="140" fill="#6366f1" fill-opacity="0.18"/>' +
      '<circle cx="150" cy="340" r="120" fill="#22d3ee" fill-opacity="0.12"/>' +
      '<text x="400" y="218" text-anchor="middle" fill="#e0e7ff" font-family="system-ui,sans-serif" font-size="32" font-weight="700">ARCHON ENGINEERING</text>' +
      "</svg>",
  );

export const handleBlogCoverError = (event: React.SyntheticEvent<HTMLImageElement>): void => {
  const img = event.currentTarget;
  if (img.dataset.fallbackApplied === "1") return;
  img.dataset.fallbackApplied = "1";
  img.src = DEFAULT_BLOG_COVER_IMAGE;
};
