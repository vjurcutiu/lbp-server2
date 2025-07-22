import React from "react";
import { BrowserRouter, Routes, Route } from "react-router-dom";
import Home from "./Home";
import PaymentSuccess from "./features/Payment/PaymentSuccess";
import PaymentCancel from "./features/Payment/PaymentCancel";
import DownloadLatest from "./features/download";


function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<Home />} />
        <Route path="/payment-success" element={<PaymentSuccess />} />
        <Route path="/payment-cancel" element={<PaymentCancel />} />
        <Route path="/download" element={<DownloadLatest />} />
      </Routes>
    </BrowserRouter>
  );
}

export default App;
