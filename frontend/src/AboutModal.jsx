import React from "react";
import AbstractModal from "./components/common/AbstractModal";

const ICON_SIZE = 64;

const AboutModal = ({ open, onClose }) => (
  <AbstractModal
    open={open}
    title={null}
    onClose={onClose}
    actions={[
      {
        label: "Close",
        onClick: onClose,
        variant: "primary"
      }
    ]}
  >
    <div
      style={{
        maxWidth: 360,
        minWidth: 280,
        margin: "0 auto",
        fontFamily: "inherit",
        textAlign: "center"
      }}
    >
      <img
        src="icon.png"
        alt="LexBot"
        style={{
          width: ICON_SIZE,
          height: ICON_SIZE,
          marginBottom: 12,
          filter: "drop-shadow(0 4px 24px #747bff55)"
        }}
      />
      <div
        style={{
          fontWeight: 700,
          fontSize: "1.19rem",
          marginBottom: 6,
          letterSpacing: ".01em"
        }}
      >
        What is LexBot?
      </div>
      <div
        style={{
          fontWeight: 400,
          fontSize: "1.04rem",
          marginBottom: 16,
          color: "#222"
        }}
      >
        LexBot is an <span style={{ color: "#747bff", fontWeight: 600 }}>AI-powered search engine</span> and document processor that helps you search through your archive and within large documents.
      </div>
      <div
        style={{
          fontWeight: 600,
          fontSize: "1.08rem",
          margin: "18px 0 6px 0",
          textAlign: "left"
        }}
      >
        Features:
      </div>
      <ul style={{ listStyle: "none", paddingLeft: 0, margin: "0 auto 16px auto" }}>
        <li style={{ display: "flex", alignItems: "center", marginBottom: 6 }}>
            <span style={{ color: "#747bff", fontSize: "1.2em", marginRight: 8 }}>•</span>
            In-document and in-archive search
        </li>
        <li style={{ display: "flex", alignItems: "center", marginBottom: 6 }}>
            <span style={{ color: "#747bff", fontSize: "1.2em", marginRight: 8 }}>•</span>
            Chat-based search interface
        </li>
        <li style={{ display: "flex", alignItems: "center", marginBottom: 6 }}>
            <span style={{ color: "#747bff", fontSize: "1.2em", marginRight: 8 }}>•</span>
            Custom metadata generation
        </li>
        </ul>
      <div style={{ margin: "10px 0 30px 0", fontSize: "0.99rem" }}>
        <span style={{ color: "#747bff", fontWeight: 600 }}>Try it free:</span> Download the demo version today and try out 50 pages and 50 messages.
      </div>
    </div>
  </AbstractModal>
);

export default AboutModal;
