"use client";

import { useState } from "react";
import { ConfirmModal } from "@/components/ui/modal";

interface UseConfirmOptions {
  title: string;
  message: string;
  confirmLabel?: string;
  cancelLabel?: string;
  variant?: "default" | "destructive";
}

export function useConfirm() {
  const [options, setOptions] = useState<UseConfirmOptions | null>(null);
  const [resolveReject, setResolveReject] = useState<{
    resolve: (value: boolean) => void;
    reject: () => void;
  } | null>(null);

  const confirm = (opts: UseConfirmOptions): Promise<boolean> => {
    return new Promise((resolve, reject) => {
      setOptions(opts);
      setResolveReject({ resolve, reject });
    });
  };

  const handleClose = () => {
    setOptions(null);
    setResolveReject(null);
  };

  const handleConfirm = () => {
    resolveReject?.resolve(true);
    handleClose();
  };

  const handleCancel = () => {
    resolveReject?.resolve(false);
    handleClose();
  };

  const ConfirmDialog = options ? (
    <ConfirmModal
      isOpen={true}
      onClose={handleCancel}
      onConfirm={handleConfirm}
      title={options.title}
      message={options.message}
      confirmLabel={options.confirmLabel}
      cancelLabel={options.cancelLabel}
      variant={options.variant}
    />
  ) : null;

  return { confirm, ConfirmDialog };
}
