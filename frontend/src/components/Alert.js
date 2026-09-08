import React from 'react';

export default function Alert({ kind = 'info', title, children, onClose }) {
  const kinds = {
    info: 'alert-info',
    success: 'alert-success',
    error: 'alert-error',
    warning: 'alert-warning',
  };
  return (
    <div className={`alert ${kinds[kind] || kinds.info}`} role="alert">
      {title && <strong>{title}</strong>}
      {children && <div>{children}</div>}
      {onClose && (
        <button type="button" className="alert-close" onClick={onClose} aria-label="Dismiss">
          ×
        </button>
      )}
    </div>
  );
}