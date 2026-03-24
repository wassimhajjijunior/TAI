import { DocumentUploadDropzone } from "@/components/upload/document-upload-dropzone";
import { Badge } from "@/components/ui/badge";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Separator } from "@/components/ui/separator";

export default function NewDocumentPage() {
  return (
    <section className="space-y-6">
      <Card className="border-primary/20 shadow-sm">
        <CardHeader>
          <div className="flex items-center gap-2">
            <Badge>Track A</Badge>
            <Badge variant="secondary">Step 1</Badge>
          </div>
          <CardTitle className="text-2xl">Document upload workspace</CardTitle>
          <CardDescription>
            Upload tender files to start ingestion and analysis. Styling now uses Tailwind + shadcn components.
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <Separator />
          <DocumentUploadDropzone />
        </CardContent>
      </Card>
    </section>
  );
}
