type DocumentRespondPageProps = {
  params: {
    id: string;
  };
};

export default function DocumentRespondPage({ params }: DocumentRespondPageProps) {
  return <div>Track B: response editor scaffold for {params.id}</div>;
}
