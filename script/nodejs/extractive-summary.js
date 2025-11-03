function extractiveSummary(text, sentenceCount) {
    if (!text) return "";

    // 1. Divide el texto en oraciones.
    const sentences = text.match(/[^\.!\?]+[\.!\?]+/g) || [];
    if (sentences.length <= sentenceCount) {
        return text;
    }

    // 2. Define palabras comunes a ignorar (stop words).
    const stopWords = new Set(['a', 'an', 'the', 'is', 'are', 'in', 'on', 'of', 'and', 'to', 'for', 'it', 'you', 'your', 'with', 'as', 'by']);

    // 3. Calcula la frecuencia de cada palabra importante.
    const wordFrequencies = {};
    const words = text.toLowerCase().replace(/[^a-z0-9\s]/g, '').split(/\s+/);
    words.forEach(word => {
        if (!stopWords.has(word)) {
            wordFrequencies[word] = (wordFrequencies[word] || 0) + 1;
        }
    });

    // 4. Puntúa cada oración.
    const sentenceScores = {};
    sentences.forEach(sentence => {
        const sentenceWords = sentence.toLowerCase().replace(/[^a-z0-9\s]/g, '').split(/\s+/);
        let score = 0;
        sentenceWords.forEach(word => {
            if (wordFrequencies[word]) {
                score += wordFrequencies[word];
            }
        });
        // Normalizamos por longitud para no favorecer excesivamente oraciones largas.
        if (sentenceWords.length > 0) {
            sentenceScores[sentence] = score / sentenceWords.length;
        } else {
            sentenceScores[sentence] = 0;
        }
    });

    // 5. Ordena y selecciona las mejores oraciones.
    const summarySentences = sentences
        .sort((a, b) => sentenceScores[b] - sentenceScores[a])
        .slice(0, sentenceCount);

    return summarySentences.join(" ");
}

// --- Texto de Entrada ---
const vpcText = `# Understanding Virtual Private Clouds (VPC)
A Virtual Private Cloud (VPC) is a virtual network dedicated to your AWS account. It is logically isolated from other virtual networks in the AWS Cloud. You can launch your AWS resources, such as Amazon EC2 instances, into your VPC. This provides a secure and isolated environment for your cloud resources, giving you complete control over your virtual networking environment.
## Key Concepts and Components of a VPC
To effectively utilize a VPC, it's crucial to understand its core components and how they interact:
### 1. Subnets
A VPC is divided into one or more subnets, which are ranges of IP addresses in your VPC. Subnets can be either public or private:
* **Public Subnets**: Resources in a public subnet can access the internet, typically through an Internet Gateway.
* **Private Subnets**: Resources in a private subnet do not have direct internet access. They are often used for databases and application servers that require enhanced security.
### 2. IP Addressing
Each VPC is assigned a Classless Inter-Domain Routing (CIDR) block. Within this block, each subnet also has its own CIDR block. AWS reserves the first four and last IP addresses in each subnet for internal use.
### 3. Route Tables
Route tables contain a set of rules, called routes, that determine where network traffic from your subnet or gateway is directed. Each subnet must be associated with a route table. The main route table is created by default, and you can create custom route tables.
### 4. Internet Gateway (IGW)
An Internet Gateway is a horizontally scaled, redundant, and highly available VPC component that allows communication between instances in your VPC and the internet. To make a subnet public, you must attach an Internet Gateway to your VPC and configure a route in the subnet's route table to direct internet-bound traffic to the IGW.
### 5. NAT Gateway (Network Address Translation Gateway)
A NAT Gateway enables instances in a private subnet to connect to the internet or other AWS services, but prevents the internet from initiating a connection with those instances. NAT Gateways are typically deployed in a public subnet and configured in the private subnet's route table as the target for internet-bound traffic.
### 6. Security Groups
Security groups act as virtual firewalls for your instances to control inbound and outbound traffic. They operate at the instance level and define rules for allowed protocols, ports, and source/destination IP addresses. Security groups are stateful, meaning if you allow inbound traffic, the outbound reply is automatically allowed.
### 7. Network Access Control Lists (Network ACLs)
Network ACLs are optional layers of security that act as a firewall for controlling traffic in and out of one or more subnets. Unlike security groups, Network ACLs are stateless, meaning you must explicitly allow both inbound and outbound traffic. They provide a finer-grained control at the subnet level.
### 8. VPC Peering
VPC peering allows you to connect two VPCs directly using private IP addresses. Instances in either VPC can communicate with each other as if they are within the same network. Peering connections are useful for sharing resources or enabling cross-VPC communication within your organization.
### 9. VPN Gateway and AWS Direct Connect
* **VPN Gateway**: Enables a secure, private connection between your VPC and your on-premises network over the public internet. This is often used for hybrid cloud architectures.
* **AWS Direct Connect**: Provides a dedicated network connection from your premises to AWS, offering consistent network performance and reduced bandwidth costs compared to internet-based VPN connections.
## Benefits of Using a VPC
* **Isolation and Security**: Your resources are isolated from other AWS customers, enhancing security and privacy.
* **Network Control**: You have complete control over your network environment, including IP address ranges, subnets, route tables, and network gateways.
* **Scalability**: Easily scale your network resources up or down to meet demand without impacting other AWS users.
* **Hybrid Cloud Capabilities**: Seamlessly integrate your on-premises data centers with your AWS cloud resources.
* **Compliance**: Helps meet various compliance requirements by providing a dedicated and highly controllable network environment.
## Common Use Cases
* **Web Applications**: Hosting multi-tier web applications with web servers in public subnets and database servers in private subnets.
* **Corporate Networks**: Extending your corporate network to the cloud securely using VPN or Direct Connect.
* **Development and Test Environments**: Creating isolated environments for development, testing, and staging.
* **High-Security Workloads**: Running applications that require strict network isolation and control, such as financial or healthcare applications.
## Conclusion
VPC is a fundamental building block for designing secure, scalable, and resilient cloud architectures on AWS. By understanding its components and capabilities, you can build a robust and customized virtual network that perfectly suits your application and business needs, providing the flexibility and control required for modern cloud deployments.`;


// --- Generar y mostrar el resumen ---
const extractiveResult = extractiveSummary(vpcText, 3); // Pedimos un resumen de 3 oraciones

console.log("--- RESUMEN EXTRACTIVO ---");
console.log(extractiveResult);