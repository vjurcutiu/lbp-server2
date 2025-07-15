// src/pages/PaymentSuccess.jsx

import React from "react";
import { useNavigate } from "react-router-dom";
import { CheckCircle2 } from "lucide-react";

const PaymentSuccess = () => {
  const navigate = useNavigate();

  return (
    <div className="flex flex-col items-center justify-center min-h-[60vh] text-center">
      <CheckCircle2 size={64} className="text-green-500 mb-6" />
      <h1 className="text-2xl font-bold mb-2">Plata a fost realizată cu succes!</h1>
      <p className="mb-4">Vă mulțumim pentru achiziție.<br />Licența va fi activată automat.</p>
      <button
        className="mt-4 px-6 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition"
        onClick={() => navigate("/")}
      >
        Înapoi la început
      </button>
    </div>
  );
};

export default PaymentSuccess;
