import React, { useEffect } from "react";
import { Bot } from "lucide-react";
import { motion, useMotionValue, useTransform, animate } from "framer-motion";

/**
 * Home page with a fullscreen gradient background and a centered, floating robot icon.
 * Pointer-tracking and floating are handled by Framer Motion.
 * Ensure Framer Motion is installed:  npm i framer-motion
 */
const Home = () => {
  // Motion values track pointer position → rotations
  const xMv = useMotionValue(-0.4); // default yaw ≈ -8°
  const yMv = useMotionValue(-0.75); // default pitch ≈ 12°

  const rotateY = useTransform(xMv, [-1, 1], [-20, 20]);
  const rotateX = useTransform(yMv, [-1, 1], [16, -16]);

  // Subtle perpetual float
  const floatMv = useMotionValue(0);
  useEffect(() => {
    const controls = animate(floatMv, [0, -8, 0, 6, 0], {
      duration: 8,
      repeat: Infinity,
      ease: "easeInOut",
    });
    return controls.stop;
  }, [floatMv]);

  // Pointer tracking
  useEffect(() => {
    function handlePointerMove(e) {
      const { innerWidth, innerHeight } = window;
      const nx = (e.clientX / innerWidth) * 2 - 1;
      const ny = (e.clientY / innerHeight) * 2 - 1;
      xMv.set(nx);
      yMv.set(ny);
    }

    function handlePointerLeave() {
      animate(xMv, -0.4, { type: "spring", stiffness: 120, damping: 15 });
      animate(yMv, -0.75, { type: "spring", stiffness: 120, damping: 15 });
    }

    window.addEventListener("pointermove", handlePointerMove);
    window.addEventListener("pointerleave", handlePointerLeave);
    return () => {
      window.removeEventListener("pointermove", handlePointerMove);
      window.removeEventListener("pointerleave", handlePointerLeave);
    };
  }, [xMv, yMv]);

  return (
    // Full-viewport wrapper
    <div
      className="fixed inset-0 flex items-center justify-center overflow-hidden"
      style={{
        background: "linear-gradient(135deg, #c9d0dc 0%, #646f7c 100%)",
        boxShadow: "inset 0 0 140px #e5e7eb, inset 0 0 240px #374151",
        height: "100%"
      }}
    >
      <div className="flex flex-col items-center" style={{ perspective: 1200 }}>
        <motion.div
          style={{
            rotateX,
            rotateY,
            y: floatMv,
            scale: 1.15,
            transformStyle: "preserve-3d",
            willChange: "transform, filter",
            filter:
              "drop-shadow(0 8px 60px #a1a6b0) drop-shadow(0 2px 24px #a5a6b5)",
          }}
          transition={{ type: "spring", stiffness: 80, damping: 15 }}
        >
          <Bot size={180} className="text-[#f6f6fa]" />
        </motion.div>

        <h1
          className="text-5xl font-extrabold tracking-tight mt-6 text-[#f7f7f9]"
          style={{
            textShadow: "0 4px 28px #aeb8c9, 0 1px 30px #7a8295",
            letterSpacing: "0.05em",
          }}
        >
          LexBot PRO
        </h1>
      </div>
    </div>
  );
};

export default Home;
