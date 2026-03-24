type DocumentExportPageProps = {
  params: {
    id: string;
  };
};

export default function DocumentExportPage({ params }: DocumentExportPageProps) {
  return <div>Track B: export options scaffold for {params.id}</div>;
}
