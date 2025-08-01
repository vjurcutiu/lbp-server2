// src/pages/PaymentCancel.jsx

import React from "react";
import { useNavigate } from "react-router-dom";
import { XCircle } from "lucide-react";

const PaymentCancel = () => {
  const navigate = useNavigate();

  return (
    <div className="flex flex-col items-center justify-center min-h-[60vh] text-center">
      <XCircle size={64} className="text-red-500 mb-6" />
      <h1 className="text-2xl font-bold mb-2">The payment has been canceled.</h1>
      <p className="mb-4">
        The transaction could not be complete. You can try again at any time.
      </p>
      <button
        className="mt-4 px-6 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition"
        onClick={() => navigate("/")}
      >
        Înapoi la început
      </button>
    </div>
  );
};

export default PaymentCancel;
