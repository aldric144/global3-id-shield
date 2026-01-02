import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { FolderOpen, ArrowLeft } from 'lucide-react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '../components/ui/card';
import { Button } from '../components/ui/button';
import { Input } from '../components/ui/input';
import { Label } from '../components/ui/label';
import { Textarea } from '../components/ui/textarea';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '../components/ui/select';
import { Alert, AlertDescription } from '../components/ui/alert';
import { api } from '../lib/api';

const caseTypes = [
  'Homicide',
  'Fraud',
  'Cybercrime',
  'Identity Theft',
  'Child Exploitation',
  'Human Trafficking',
  'Terrorism',
  'Financial Crime',
  'Drug Trafficking',
  'Other'
];

export function NewCasePage() {
  const navigate = useNavigate();
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState('');
  
  const [formData, setFormData] = useState({
    title: '',
    description: '',
    case_type: '',
    priority: 'medium',
    incident_date: '',
    incident_location: ''
  });

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    setIsLoading(true);

    try {
      const newCase = await api.createCase({
        ...formData,
        incident_date: formData.incident_date || undefined,
        incident_location: formData.incident_location || undefined
      });
      navigate(`/cases/${newCase.id}`);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to create case');
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="max-w-2xl mx-auto space-y-6">
      <div className="flex items-center gap-4">
        <Button variant="ghost" size="icon" onClick={() => navigate('/cases')}>
          <ArrowLeft className="w-5 h-5" />
        </Button>
        <div>
          <h1 className="text-2xl font-bold text-foreground">Create New Case</h1>
          <p className="text-muted-foreground">
            Initialize a new forensic investigation case
          </p>
        </div>
      </div>

      <Card className="bg-card border-border">
        <CardHeader>
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-lg bg-primary/20 flex items-center justify-center">
              <FolderOpen className="w-5 h-5 text-primary" />
            </div>
            <div>
              <CardTitle>Case Information</CardTitle>
              <CardDescription>
                Enter the details for the new investigation case
              </CardDescription>
            </div>
          </div>
        </CardHeader>
        <CardContent>
          <form onSubmit={handleSubmit} className="space-y-6">
            {error && (
              <Alert variant="destructive">
                <AlertDescription>{error}</AlertDescription>
              </Alert>
            )}

            <div className="space-y-2">
              <Label htmlFor="title">Case Title *</Label>
              <Input
                id="title"
                placeholder="Enter case title"
                value={formData.title}
                onChange={(e) => setFormData({ ...formData, title: e.target.value })}
                required
                className="bg-input border-border"
              />
            </div>

            <div className="space-y-2">
              <Label htmlFor="description">Description</Label>
              <Textarea
                id="description"
                placeholder="Enter case description"
                value={formData.description}
                onChange={(e) => setFormData({ ...formData, description: e.target.value })}
                rows={4}
                className="bg-input border-border"
              />
            </div>

            <div className="grid grid-cols-2 gap-4">
              <div className="space-y-2">
                <Label htmlFor="case_type">Case Type *</Label>
                <Select
                  value={formData.case_type}
                  onValueChange={(value) => setFormData({ ...formData, case_type: value })}
                  required
                >
                  <SelectTrigger className="bg-input border-border">
                    <SelectValue placeholder="Select type" />
                  </SelectTrigger>
                  <SelectContent>
                    {caseTypes.map((type) => (
                      <SelectItem key={type} value={type}>{type}</SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>

              <div className="space-y-2">
                <Label htmlFor="priority">Priority *</Label>
                <Select
                  value={formData.priority}
                  onValueChange={(value) => setFormData({ ...formData, priority: value })}
                >
                  <SelectTrigger className="bg-input border-border">
                    <SelectValue placeholder="Select priority" />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="low">Low</SelectItem>
                    <SelectItem value="medium">Medium</SelectItem>
                    <SelectItem value="high">High</SelectItem>
                    <SelectItem value="critical">Critical</SelectItem>
                  </SelectContent>
                </Select>
              </div>
            </div>

            <div className="grid grid-cols-2 gap-4">
              <div className="space-y-2">
                <Label htmlFor="incident_date">Incident Date</Label>
                <Input
                  id="incident_date"
                  type="datetime-local"
                  value={formData.incident_date}
                  onChange={(e) => setFormData({ ...formData, incident_date: e.target.value })}
                  className="bg-input border-border"
                />
              </div>

              <div className="space-y-2">
                <Label htmlFor="incident_location">Incident Location</Label>
                <Input
                  id="incident_location"
                  placeholder="Enter location"
                  value={formData.incident_location}
                  onChange={(e) => setFormData({ ...formData, incident_location: e.target.value })}
                  className="bg-input border-border"
                />
              </div>
            </div>

            <div className="flex items-center justify-end gap-3 pt-4 border-t border-border">
              <Button type="button" variant="outline" onClick={() => navigate('/cases')}>
                Cancel
              </Button>
              <Button type="submit" disabled={isLoading || !formData.title || !formData.case_type}>
                {isLoading ? 'Creating...' : 'Create Case'}
              </Button>
            </div>
          </form>
        </CardContent>
      </Card>

      <div className="p-4 rounded-lg bg-muted/50 border border-border">
        <p className="text-xs text-muted-foreground">
          All case creation actions are logged for chain-of-custody compliance. 
          A unique case number will be automatically generated upon creation.
        </p>
      </div>
    </div>
  );
}
