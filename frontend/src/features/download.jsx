import { useEffect, useState } from "react";
import { Bot, Download } from "lucide-react";

const LATEST_RELEASE_API = "https://api.github.com/repos/vjurcutiu/lbp2/releases/latest";

export default function DownloadLatest() {
  const [error, setError] = useState(null);
  const [release, setRelease] = useState(null);
  const [downloading, setDownloading] = useState(true);

  useEffect(() => {
    fetch(LATEST_RELEASE_API)
      .then(res => res.json())
      .then(data => {
        setRelease(data);
        const asset = data.assets.find(a =>
          a.name.endsWith('.exe') // or your main filetype
        );
        if (asset) {
          setTimeout(() => { // Delay to show animation
            window.location.href = asset.browser_download_url;
            setDownloading(false);
          }, 1500);
        } else {
          setError("No downloadable asset found.");
          setDownloading(false);
        }
      })
      .catch(() => {
        setError("Failed to fetch release info.");
        setDownloading(false);
      });
  }, []);

  return (
    <div
      style={{
        minHeight: "100vh",
        background: "#fff",
        color: "#222",
        display: "flex",
        flexDirection: "column",
        alignItems: "center",
        justifyContent: "center",
        fontFamily: "sans-serif",
        padding: 24,
      }}
    >
      <div style={{ marginBottom: 18 }}>
            <img
            src="icon.png"
            alt="LexBot"
            style={{
                filter: "drop-shadow(0 4px 24px #747bff66)",
                width: "88px",
                height: "88px",
            }}
            />      
        </div>
      <div style={{ fontWeight: 800, fontSize: "2.1rem", marginBottom: 8 }}>Downloading LexBot PRO</div>
      {release && (
        <div style={{ marginBottom: 16, color: "#747bff", fontWeight: 500 }}>
          {release.tag_name && <span>Version <b>{release.tag_name}</b></span>}{" "}
          {release.published_at && (
            <span style={{ color: "#888", fontWeight: 400 }}>
              &middot; {new Date(release.published_at).toLocaleDateString()}
            </span>
          )}
        </div>
      )}
      <div style={{ fontSize: "1.08rem", marginBottom: 16, textAlign: "center" }}>
        Thank you for choosing LexBot PRO!<br />
        Your download will begin automatically.
      </div>
      {downloading ? (
        <div style={{ display: "flex", gap: 12, alignItems: "center", marginBottom: 24 }}>
          <Download className="spin" color="#747bff" size={28} />
          <span style={{ color: "#747bff", fontWeight: 600 }}>Preparing download...</span>
          <style>
            {`
              .spin { animation: spin 1.2s linear infinite; }
              @keyframes spin { to { transform: rotate(360deg); } }
            `}
          </style>
        </div>
      ) : null}
      {error ? (
        <div style={{ color: "#e25555", marginBottom: 14 }}>{error}</div>
      ) : (
        release &&
        <a
          href={release.html_url}
          target="_blank"
          rel="noopener noreferrer"
          style={{
            display: "inline-block",
            padding: "10px 28px",
            background: "#747bff",
            color: "#fff",
            borderRadius: 14,
            textDecoration: "none",
            fontWeight: 600,
            letterSpacing: ".03em",
            marginTop: 8,
            boxShadow: "0 2px 8px #747bff22"
          }}
        >
          Download didn’t start? Click here
        </a>
      )}
    </div>
  );
}
