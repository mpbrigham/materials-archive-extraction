module.exports = {
    // Flow file
    flowFile: '/data/flows.json',
    
    // User directory
    userDir: '/data/',
    
    // Node-RED scans the `nodes` directory in the userDir to find nodes
    nodesDir: '/data/nodes',
    
    // Logging
    logging: {
        console: {
            level: "info",
            metrics: false,
            audit: false
        }
    },
    
    // Disable editor to run in headless mode (optional)
    // editorEnabled: false,
    
    // Function node settings
    functionGlobalContext: {
        // Add any global modules here
    },
    
    // Allow function nodes to load external modules
    functionExternalModules: true,
    
    // Debug max message length
    debugMaxLength: 10000,
    
    // HTTP settings
    httpAdminRoot: '/',
    httpNodeRoot: '/',
    
    // Security
    credentialSecret: process.env.NODE_RED_CREDENTIAL_SECRET
}
