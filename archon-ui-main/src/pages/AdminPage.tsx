import React from "react";

import { Tabs, TabsContent, TabsList, TabsTrigger } from "../features/ui/primitives/tabs";

export const AdminPage: React.FC = () => {
    // In a real app, this would be the place for "System Health" and "Settings" tabs too
    return (
        <div className="container mx-auto py-8">
            <h1 className="text-3xl font-bold mb-6">Admin Console</h1>
            
            <Tabs defaultValue="users" className="w-full">
                <TabsList className="mb-4">
                    <TabsTrigger value="users">User Management</TabsTrigger>
                    {/* Future Tabs: System Health, Logs */}
                </TabsList>
                
                <TabsContent value="users">
                    <div className="p-4 border rounded bg-muted/20">
                        <p className="text-muted-foreground">User Management has been moved to the main application's Admin Portal (Port 5173).</p>
                    </div>
                </TabsContent>
            </Tabs>
        </div>
    );
};
