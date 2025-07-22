// AbstractModal.jsx
import React from 'react';
import './AbstractModal.css';
/**
 * AbstractModal Component
 */
const AbstractModal = ({ open, title, children, onClose, actions }) => {
  if (!open) return null; // <--- add this line!
  return (
    <div
      className="modal-overlay fixed inset-0 flex items-center justify-center"
      onClick={onClose}
    >
      <div
        className="modal-content bg-white p-6 rounded-2xl shadow-lg"
        onClick={(e) => e.stopPropagation()}
      >
        <h3 className="mb-4 text-xl font-semibold">{title}</h3>
        <div className="mb-6">
          {children}
        </div>
        <div className="flex justify-end space-x-2">
          {actions.map((action, idx) => (
            <button
              key={idx}
              onClick={action.onClick}
              className={`px-4 py-2 rounded-lg ${
                action.variant === 'primary'
                  ? 'bg-gray-800 text-white'
                  : 'bg-gray-300 text-gray-800'
              }`}
            >
              {action.label}
            </button>
          ))}
        </div>
      </div>
    </div>
  );
};


export default AbstractModal;
