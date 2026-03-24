type DocumentDetailPageProps = {
  params: {
    id: string;
  };
};

export default function DocumentDetailPage({ params }: DocumentDetailPageProps) {
  return <div>Track A: document detail scaffold for {params.id}</div>;
}
