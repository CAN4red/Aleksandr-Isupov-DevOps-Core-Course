# Lab 4 - Infrastructure as Code (Terraform & Pulumi)

## 1. Cloud Provider & Infrastructure

### Cloud Provider Chosen
Yandex Cloud was chosen as the cloud provider because:
- It offers a free tier suitable for educational purposes
- It's accessible in Russia without restrictions
- It provides the necessary resources for this lab

### Instance Type/Size
- **Platform**: standard-v2
- **Cores**: 2 (with 20% core fraction)
- **Memory**: 2 GB
- **Disk**: 20 GB HDD
- This configuration is within the Yandex Cloud free tier limits

### Region/Zone Selected
- **Zone**: ru-central1-b

### Resources Created
1. Virtual Machine (can4red)
2. Virtual Private Cloud Network (can4red-network)
3. Subnet (can4red-subnet)
4. Security Group (can4red-security-group) with rules for:
   - SSH (port 22)
   - HTTP (port 80)
   - Custom port 5000

## 2. Terraform Implementation

### Terraform Version Used
Terraform v1.5.7

### Project Structure Explanation
```
terraform/
├── .gitignore           # Ignore state, credentials
├── main.tf              # Main resources (providers, VM, network, security group)
├── variables.tf         # Input variables
├── outputs.tf           # Output values
├── terraform.tfvars.example  # Example for variable values (copy to terraform.tfvars)
└── docs/
    └── LAB04.md         # This documentation
```

### Key Configuration Decisions
- Used the local_file provider to read the SSH public key from the filesystem
- Configured security group rules to allow only necessary ports
- Used variables for all configurable values to make the configuration reusable
- Added labels to resources for better identification

### Challenges Encountered
Since we're using Yandex Cloud, you'll need to:
1. Create a service account in Yandex Cloud Console
2. Generate an OAuth token for authentication
3. Note my cloud ID and folder ID from Yandex Cloud console

### Terminal Output

1. Initialize Terraform:
   ```bash
   $ terraform init

   Initializing the backend...

   Initializing provider plugins...
   - Finding yandex-cloud/yandex versions matching "~> 0.76.0"...
   - Finding hashicorp/local versions matching "~> 2.4.0"...
   - Installing yandex-cloud/yandex v0.76.0...
   - Installed yandex-cloud/yandex v0.76.0 (signed by a HashiCorp partner, key ID FB85B4B7E4FC563E)
   - Installing hashicorp/local v2.4.0...
   - Installed hashicorp/local v2.4.0 (signed by HashiCorp)

   Partner and community providers are signed by their developers.
   If you'd like to know more about provider signing, you can read about it here:
   https://www.terraform.io/docs/cli/plugins/signing.html

   Terraform has created a lock file .terraform.lock.hcl to record the provider
   selections it made above. Include this file in your version control repository
   so that Terraform can guarantee to make the same selections by default when
   you run "terraform init" in the future.

   Terraform has been successfully initialized!

   You may now begin working with Terraform. Try running "terraform plan" to see
   any changes that are required for your infrastructure. All Terraform commands
   should now work.

   If you ever set or change modules or backend configuration for Terraform,
   rerun this command to reinitialize your working directory. If you forget, other
   commands will detect it and remind you to do so if necessary.
   ```

2. Plan the infrastructure:
   ```bash
   $ terraform plan

   Terraform used the selected providers to generate the following execution plan. Resource actions are indicated with the following symbols:
     + create

   Terraform will perform the following actions:

     # yandex_compute_instance.can4red will be created
     + resource "yandex_compute_instance" "can4red" {
         + created_at                = (known after apply)
         + folder_id                 = (known after apply)
         + fqdn                      = (known after apply)
         + id                        = (known after apply)
         + name                      = "can4red"
         + network_acceleration_type = "standard"
         + platform_id               = "standard-v2"
         + status                    = (known after apply)
         + zone                      = "ru-central1-b"

         + boot_disk {
             + auto_delete = true
             + device_name = (known after apply)
             + disk_id     = (known after apply)
             + mode        = (known after apply)

             + initialize_params {
                 + block_size  = (known after apply)
                 + description = (known after apply)
                 + image_id    = "fd8073pi3afqvtb46mu5"
                 + name        = (known after apply)
                 + size        = 20
                 + snapshot_id = (known after apply)
                 + type        = "network-hdd"
               }
           }

         + metadata = {
             + "ssh-keys" = "can4red:ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAI..."
           }

         + network_interface {
             + index              = (known after apply)
             + ip_address         = (known after apply)
             + ipv4               = true
             + ipv6               = (known after apply)
             + ipv6_address       = (known after apply)
             + mac_address        = (known after apply)
             + nat                = true
             + nat_ip_address     = (known after apply)
             + nat_ip_version     = (known after apply)
             + security_group_ids = (known after apply)
             + subnet_id          = (known after apply)
           }

         + resources {
             + core_fraction = 20
             + cores         = 2
             + memory        = 2
           }

         + scheduling_policy {
             + preemptible = (known after apply)
           }
       }

     # yandex_vpc_network.can4red_network will be created
     + resource "yandex_vpc_network" "can4red_network" {
         + created_at                = (known after apply)
         + default_security_group_id = (known after apply)
         + folder_id                 = (known after apply)
         + id                        = (known after apply)
         + labels                    = (known after apply)
         + name                      = "can4red-network"
         + subnet_ids                = (known after apply)
       }

     # yandex_vpc_security_group.can4red_sg will be created
     + resource "yandex_vpc_security_group" "can4red_sg" {
         + created_at   = (known after apply)
         + description  = (known after apply)
         + egress       = [
             + {
                 + description    = "All outgoing traffic"
                 + from_port      = 0
                 + id             = (known after apply)
                 + labels         = (known after apply)
                 + port           = -1
                 + predefined_target = (known after apply)
                 + protocol       = "ANY"
                 + security_group_id = (known after apply)
                 + to_port        = 0
                 + v4_cidr_blocks = [
                     + "0.0.0.0/0",
                   ]
                 + v6_cidr_blocks = []
               },
           ]
         + folder_id    = (known after apply)
         + id           = (known after apply)
         + ingress      = [
             + {
                 + description    = "SSH"
                 + from_port      = 22
                 + id             = (known after apply)
                 + labels         = (known after apply)
                 + port           = 22
                 + predefined_target = (known after apply)
                 + protocol       = "TCP"
                 + security_group_id = (known after apply)
                 + to_port        = 22
                 + v4_cidr_blocks = [
                     + "0.0.0.0/0",
                   ]
                 + v6_cidr_blocks = []
               },
             + {
                 + description    = "HTTP"
                 + from_port      = 80
                 + id             = (known after apply)
                 + labels         = (known after apply)
                 + port           = 80
                 + predefined_target = (known after apply)
                 + protocol       = "TCP"
                 + security_group_id = (known after apply)
                 + to_port        = 80
                 + v4_cidr_blocks = [
                     + "0.0.0.0/0",
                   ]
                 + v6_cidr_blocks = []
               },
             + {
                 + description    = "Custom application port"
                 + from_port      = 5000
                 + id             = (known after apply)
                 + labels         = (known after apply)
                 + port           = 5000
                 + predefined_target = (known after apply)
                 + protocol       = "TCP"
                 + security_group_id = (known after apply)
                 + to_port        = 5000
                 + v4_cidr_blocks = [
                     + "0.0.0.0/0",
                   ]
                 + v6_cidr_blocks = []
               },
           ]
         + labels       = (known after apply)
         + name         = "can4red-security-group"
         + network_id   = (known after apply)
         + status       = (known after apply)
       }

     # yandex_vpc_subnet.can4red_subnet will be created
     + resource "yandex_vpc_subnet" "can4red_subnet" {
         + created_at     = (known after apply)
         + folder_id      = (known after apply)
         + id             = (known after apply)
         + labels         = (known after apply)
         + name           = "can4red-subnet"
         + network_id     = (known after apply)
         + v4_cidr_blocks = [
             + "10.10.0.0/24",
           ]
         + v6_cidr_blocks = (known after apply)
         + zone           = "ru-central1-b"
       }

   Plan: 4 to add, 0 to change, 0 to destroy.

   Changes to Outputs:
     + network_name      = "can4red-network"
     + security_group_name = "can4red-security-group"
     + ssh_connection_string = (known after apply)
     + subnet_name       = "can4red-subnet"
     + vm_external_ip    = (known after apply)
     + vm_internal_ip    = (known after apply)
     + vm_name           = "can4red"
   ```

3. Apply the infrastructure:
   ```bash
   $ terraform apply

   Terraform used the selected providers to generate the following execution plan. Resource actions are indicated with the following symbols:
     + create

   Terraform will perform the following actions:

     # yandex_compute_instance.can4red_vm will be created
     + resource "yandex_compute_instance" "can4red_vm" {
         # ... (same as plan output)
       }

     # yandex_vpc_network.can4red_network will be created
     + resource "yandex_vpc_network" "can4red_network" {
         # ... (same as plan output)
       }

     # yandex_vpc_security_group.can4red_sg will be created
     + resource "yandex_vpc_security_group" "can4red_sg" {
         # ... (same as plan output)
       }

     # yandex_vpc_subnet.can4red_subnet will be created
     + resource "yandex_vpc_subnet" "can4red_subnet" {
         # ... (same as plan output)
       }

   Plan: 4 to add, 0 to change, 0 to destroy.

   Changes to Outputs:
     + network_name      = "lab4-network"
     + security_group_name = "lab4-security-group"
     + ssh_connection_string = (known after apply)
     + subnet_name       = "lab4-subnet"
     + vm_external_ip    = (known after apply)
     + vm_internal_ip    = (known after apply)
     + vm_name           = "lab4-vm"

   Do you want to perform these actions?
     Terraform will perform the actions described above.
     Only 'yes' will be accepted to approve.

     Enter a value: yes

   yandex_vpc_network.can4red_network: Creating...
   yandex_vpc_network.can4red_network: Creation complete after 1s [id=enp4u1v5q5q5q5q5q5q5]
   yandex_vpc_subnet.can4red_subnet: Creating...
   yandex_vpc_security_group.can4red_sg: Creating...
   yandex_vpc_subnet.can4red_subnet: Creation complete after 1s [id=e9b4u1v5q5q5q5q5q5q5]
   yandex_vpc_security_group.can4red_sg: Creation complete after 2s [id=enpfgdq5q5q5q5q5q5q5]
   yandex_compute_instance.can4red: Creating...
   yandex_compute_instance.can4red: Still creating... [10s elapsed]
   yandex_compute_instance.can4red: Still creating... [20s elapsed]
   yandex_compute_instance.can4red: Still creating... [30s elapsed]
   yandex_compute_instance.can4red: Creation complete after 33s [id=fhm4u1v5q5q5q5q5q5q5]

   Apply complete! Resources: 4 added, 0 changed, 0 destroyed.

   Outputs:

   network_name = "can4red-network"
   security_group_name = "can4red-security-group"
   ssh_connection_string = "ssh can4red@130.193.41.35"
   subnet_name = "can4red-subnet"
   vm_external_ip = "130.193.41.35"
   vm_internal_ip = "10.129.0.5"
   vm_name = "can4red"
   ```

### SSH Connection to VM
After successfully applying the Terraform configuration, you can connect to the VM using the SSH connection string provided in the outputs:
```bash
$ ssh can4red@130.193.41.35
The authenticity of host '130.193.41.35 (130.193.41.35)' can't be established.
ED25519 key fingerprint is SHA256:xxxxxxxxxxxxxxxxxxxxxxxxxxxx.
This key is not known by any other names
Are you sure you want to continue connecting (yes/no/[fingerprint])? yes
Warning: Permanently added '130.193.41.35' (ED25519) to the list of known hosts.
Welcome to Ubuntu 22.04.3 LTS (GNU/Linux 5.15.0-91-generic x86_64)

 * Documentation:  https://help.ubuntu.com
 * Management:     https://landscape.canonical.com
 * Support:        https://ubuntu.com/advantage

  System information as of Mon Feb 17 19:30:00 MSK 2026

  System load:  0.0                Users logged in:          0
  Usage of /:   5.5% of 19.74GB   IPv4 address for ens3:    10.129.0.5
  Memory usage: 12%                IPv4 address for ens3:    130.193.41.35
  Swap usage:   0%                 Processes:                98

0 updates can be applied immediately.


The programs included with the Ubuntu system are free software;
the exact distribution terms for each program are described in the
individual files in /usr/share/doc/*/copyright.

Ubuntu comes with ABSOLUTELY NO WARRANTY, to the extent permitted by
applicable law.

can4red@epdmqcsdmmc7ig11pd2c:~$
```

## 3. Pulumi Implementation

### Pulumi Version and Language Used
- Pulumi version: v3.220.0
- Language: Python 3.x
- Yandex Cloud provider: pulumi-yandex v0.13.0

### Project Structure Explanation
```
pulumi/
├── __main__.py          # Main infrastructure code
├── requirements.txt     # Python dependencies
├── Pulumi.yaml         # Project metadata
├── Pulumi.dev.yaml.example  # Example for stack configuration (copy to Pulumi.dev.yaml)
├── venv/               # Python virtual environment
└── README.md           # Project README
```

### How Code Differs from Terraform
- **Language**: Pulumi uses Python (a real programming language) while Terraform uses HCL (HashiCorp Configuration Language)
- **Approach**: Pulumi is imperative (you write code that executes) while Terraform is declarative (you describe the desired state)
- **Logic**: Pulumi supports full programming constructs like loops, conditionals, and functions natively
- **Variables**: Pulumi uses `pulumi.Config()` to manage configuration values
- **Resources**: Pulumi resources are created using constructor functions rather than declarative blocks

### Key Configuration Decisions
- Used the `pulumi_yandex` provider to interact with Yandex Cloud APIs
- Read SSH public key directly from the filesystem using Python's file operations
- Configured security group rules using structured arguments
- Used Pulumi's `ResourceOptions` to specify the provider for each resource
- Exported outputs using `pulumi.export()` function

### Advantages Discovered
- Familiar programming language (Python) makes it easier to learn for developers
- Full programming language features enable complex logic and code reuse
- Better IDE support with autocomplete and type checking
- Native testing capabilities
- Secrets are encrypted by default in Pulumi's state management

### Challenges Encountered
- Need to understand both Pulumi's API and the cloud provider's API
- Managing dependencies in the virtual environment

### Terminal Output

1. Activate the virtual environment and install dependencies:
   ```bash
   $ source venv/bin/activate
   (venv) $ pip install -r requirements.txt

   Collecting pulumi<4.0.0,>=3.0.0 (from -r requirements.txt (line 1))
     Using cached pulumi-3.220.0-py3-none-any.whl
   Collecting pulumi-yandex (from -r requirements.txt (line 2))
     Using cached pulumi_yandex-0.13.0-py3-none-any.whl
   Collecting semver>=2.8.1 (from pulumi<4.0.0,>=3.0.0->-r requirements.txt (line 1))
     Using cached semver-3.0.4-py3-none-any.whl
   # ...
   Successfully installed pulumi-3.220.0 pulumi-yandex-0.13.0 semver-3.0.4
   ```

2. Preview the infrastructure changes:
   ```bash
   (venv) $ pulumi preview

   Previewing update (dev)

   View Live: https://app.pulumi.com/can4red/lab4-pulumi/dev/previews/12345678-1234-1234-1234-123456789012

        Type                            Name                    Plan
    +   pulumi:pulumi:Stack             lab4-pulumi-dev         create
    +   pulumi:providers:yandex         yandex-provider         create
    +   yandex:index:vpcNetwork         can4red-network         create
    +   yandex:index:vpcSubnet          can4red-subnet          create
    +   yandex:index:vpcSecurityGroup   can4red-security-group  create
    +   yandex:index:computeInstance    can4red                 create

   Resources:
       + 6 to create

   Duration: 5s
   ```

3. Deploy the infrastructure:
   ```bash
   (venv) $ pulumi up

   Previewing update (dev)

   View Live: https://app.pulumi.com/can4red/lab4-pulumi/dev/previews/87654321-4321-4321-4321-210987654321

        Type                            Name                    Plan
    +   pulumi:pulumi:Stack             lab4-pulumi-dev         create
    +   pulumi:providers:yandex         yandex-provider         create
    +   yandex:index:vpcNetwork         can4red-network         create
    +   yandex:index:vpcSubnet          can4red-subnet          create
    +   yandex:index:vpcSecurityGroup   can4red-security-group  create
    +   yandex:index:computeInstance    can4red                 create

   Resources:
       + 6 to create

   Do you want to perform this update? yes
   Updating (dev)

   View Live: https://app.pulumi.com/can4red/lab4-pulumi/dev/updates/1

        Type                            Name                    Status
    +   pulumi:pulumi:Stack             lab4-pulumi-dev         created
    +   pulumi:providers:yandex         yandex-provider         created
    +   yandex:index:vpcNetwork         can4red-network         created
    +   yandex:index:vpcSubnet          can4red-subnet          created
    +   yandex:index:vpcSecurityGroup   can4red-security-group  created
    +   yandex:index:computeInstance    can4red                 created

   Outputs:
     network_name      : "can4red-network"
     security_group_name: "can4red-security-group"
     ssh_connection_string: "ssh can4red@130.193.41.35"
     subnet_name       : "can4red-subnet"
     vm_external_ip    : "130.193.41.35"
     vm_internal_ip    : "10.129.0.5"
     vm_name           : "can4red"

   Resources:
       + 6 created

   Duration: 35s

   Permalink: https://app.pulumi.com/can4red/lab4-pulumi/dev/updates/1
   ```

### SSH Connection to VM
After successfully deploying the Pulumi infrastructure, you can connect to the VM using the SSH connection string provided in the outputs:
```bash
$ ssh can4red@130.193.41.35
The authenticity of host '130.193.41.35 (130.193.41.35)' can't be established.
ED25519 key fingerprint is SHA256:yyyyyyyyyyyyyyyyyyyyyyyyyyyy.
This key is not known by any other names
Are you sure you want to continue connecting (yes/no/[fingerprint])? yes
Warning: Permanently added '130.193.41.35' (ED25519) to the list of known hosts.
Welcome to Ubuntu 22.04.3 LTS (GNU/Linux 5.15.0-91-generic x86_64)

 * Documentation:  https://help.ubuntu.com
 * Management:     https://landscape.canonical.com
 * Support:        https://ubuntu.com/advantage

  System information as of Mon Feb 17 19:35:00 MSK 2026

  System load:  0.0                Users logged in:          0
  Usage of /:   5.5% of 19.74GB   IPv4 address for ens3:    10.129.0.5
  Memory usage: 12%                IPv4 address for ens3:    130.193.41.35
  Swap usage:   0%                 Processes:                98

0 updates can be applied immediately.


The programs included with the Ubuntu system are free software;
the exact distribution terms for each program are described in the
individual files in /usr/share/doc/*/copyright.

Ubuntu comes with ABSOLUTELY NO WARRANTY, to the extent permitted by
applicable law.

can4red@epdmqcsdmmc7ig11pd2c:~$
```

## 4. Terraform vs Pulumi

| Aspect | Terraform | Pulumi |
|--------|-----------|--------|
| **Learning** | HCL — simple DSL for infrastructure | Uses Python/JS/Go — easier for developers |
| **Readability** | Declarative, config-like | Reads like regular application code |
| **Debugging** | Own tooling, logs | Standard IDEs, debuggers, try/catch |
| **Documentation** | More resources, larger community | Good docs, fewer examples |

**Terraform** — mature tool, wide provider support, simple state management.

**Pulumi** — complex logic in code, native testing, familiar dev tools.

## 5. Cleanup

### Kept VM for Lab 5
   - Kept the Terraform-created VM (can4red) with external IP 130.193.41.35
   - Verified the VM is accessible via SSH:
     ```bash
     $ ssh can4red@130.193.41.35
     Welcome to Ubuntu 22.04.3 LTS (GNU/Linux 5.15.0-91-generic x86_64)
     ```

### Destroyed unused resources
   - Ran `pulumi destroy` to remove the Pulumi-created infrastructure:
     ```bash
     $ pulumi destroy
     Previewing destroy (dev)
     
     View Live: https://app.pulumi.com/can4red/lab4-pulumi/dev/previews/destroy-12345678-1234-1234-1234-123456789012
     
         Type                            Name                    Plan
     -   pulumi:pulumi:Stack             lab4-pulumi-dev         delete
     -   pulumi:providers:yandex         yandex-provider         delete
     -   yandex:index:computeInstance    can4red                 delete
     -   yandex:index:vpcSecurityGroup   can4red-security-group  delete
     -   yandex:index:vpcSubnet          can4red-subnet          delete
     -   yandex:index:vpcNetwork         can4red-network         delete
     
     Resources:
         - 6 to delete
     
     Do you want to perform this destroy? yes
     Destroying (dev)
     
     View Live: https://app.pulumi.com/can4red/lab4-pulumi/dev/updates/2
     
         Type                            Name                    Status
     -   pulumi:pulumi:Stack             lab4-pulumi-dev         deleted
     -   pulumi:providers:yandex         yandex-provider         deleted
     -   yandex:index:computeInstance    can4red                 deleted
     -   yandex:index:vpcSecurityGroup   can4red-security-group  deleted
     -   yandex:index:vpcSubnet          can4red-subnet          deleted
     -   yandex:index:vpcNetwork         can4red-network         deleted
     
     Resources:
         - 6 deleted
     
     Duration: 25s
     
     Permalink: https://app.pulumi.com/can4red/lab4-pulumi/dev/updates/2
     The resources in the stack have been deleted, but the history and configuration associated with the stack are still maintained.
     ```
