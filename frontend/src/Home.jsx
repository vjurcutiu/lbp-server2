import React, { useState } from "react";
import AboutModal from "./AboutModal";
import { Bot } from "lucide-react";

const ICON_SIZE = 120;
const HOVER_COLOR = "#747bff";

function MenuLink({ href, children, onClick }) {
  const [hovered, setHovered] = useState(false);
  return (
    <a
      href={href}
      onClick={onClick}
      style={{
        color: hovered ? HOVER_COLOR : "#222",
        fontWeight: 500,
        fontSize: "1.1rem",
        textDecoration: "none",
        marginRight: children === "About" ? 24 : 0,
        letterSpacing: "0.04em",
        opacity: 0.92,
        transition: "color 0.18s, opacity 0.2s",
        cursor: "pointer",
      }}
      onMouseEnter={() => setHovered(true)}
      onMouseLeave={() => setHovered(false)}
    >
      {children}
    </a>
  );
}

const Home = () => {
  const [aboutOpen, setAboutOpen] = useState(false);

  return (
    <div
      style={{
        minHeight: "100vh",
        background: "#fff",
        color: "#222",
        fontFamily: "sans-serif",
        
      }}
    >
      {/* Header */}
      <header
        style={{
          width: "100vw",
          position: "absolute",
          top: 0,
          left: 0,
          display: "flex",
          justifyContent: "flex-end",
          alignItems: "center",
          padding: "32px 48px 0 0",
          background: "rgba(255,255,255,0.02)",
          backdropFilter: "blur(2px)",
          zIndex: 100,
          gap: "24px",
          boxSizing: "border-box",
          height: 90,
        }}
      >
        <MenuLink
          href="#"
          onClick={e => {
            e.preventDefault();
            setAboutOpen(true);
          }}
        >
          about
        </MenuLink>
        <MenuLink href="/download">download</MenuLink>
      </header>

      {/* Centered icon with absolutely positioned text above */}
      <div
        style={{
          height: "100vh",
          width: "100vw",
          display: "flex",
          alignItems: "center",
          justifyContent: "center",
          position: "relative",
        }}
      >
        {/* Text above the icon, absolutely positioned */}
        <div
          style={{
            position: "absolute",
            top: "calc(50% - 96px)",
            left: "50%",
            transform: "translate(-50%, -100%)",
            fontSize: "2.1rem",
            fontWeight: 800,
            letterSpacing: "0.06em",
            color: "#222",
            textShadow: "0 1px 4px #fff, 0 2px 12px #eee",
            pointerEvents: "none",
          }}
        >
          LexBot PRO
        </div>
        {/* Icon dead center */}
        <div>
          <img src="icon.png" alt="LexBot" style={{ width: ICON_SIZE, height: ICON_SIZE }} />
          {/* <Bot size={ICON_SIZE} color="#222" /> */}
        </div>
      </div>

      {/* Modal */}
      <AboutModal open={aboutOpen} onClose={() => setAboutOpen(false)} />
    </div>
  );
};

export default Home;
