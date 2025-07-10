function formatDate(dateStr) {
    if (!dateStr) return '';
    const date = new Date(dateStr);
    if (isNaN(date)) return '';
    return date.toISOString().split('T')[0];
}




document.addEventListener("DOMContentLoaded", function () {
    console.log("✅ DOM ready");
    const input = document.getElementById("client_id");
    console.log("🔍 client_id input:", input);
    const lookupForm = document.getElementById("lookupForm");
    if (lookupForm) {
        lookupForm.addEventListener("submit", function(event) {
            event.preventDefault();
            
            const clientId = document.getElementById("clientId").value;
            const includeCompliance = document.getElementById("includeCompliance").checked;
            
            let apiUrl = `/client/${clientId}`;
            
            if (includeCompliance) {
                apiUrl += "?include_compliance=true";
            }

            fetch(apiUrl)
                .then(response => response.json())
                .then(data => {
                    if (data.error) {
                        alert("Client not found");
                        return;
                    }

                    document.getElementById("field-client-id").textContent = data.Client_id;
                    document.getElementById("field-name").textContent = data.Name;
                    document.getElementById("field-nationality").textContent = data.Nationality;
                    document.getElementById("field-contact").textContent = data.Contact_number;
                    document.getElementById("field-email").textContent = data.Email_address;

                    document.getElementById("clientDetails").style.display = "block";

                    if (includeCompliance) {
                        document.getElementById("field-onboarded").textContent = data.Onboarded_date || 'N/A';
                        document.getElementById("field-service").textContent = data.Service_type || 'N/A';
                        document.getElementById("field-client-type").textContent = data.Client_type || 'N/A';
                        document.getElementById("field-pep").textContent = data.Pep || 'N/A';
                        document.getElementById("field-risk").textContent = data.Risk_rating || 'N/A';
                        document.getElementById("field-last-assessment").textContent = data.Last_periodic_risk_assessment || 'N/A';
                        document.getElementById("field-next-assessment").textContent = data.Next_periodic_risk_assessment || 'N/A';
                        document.getElementById("field-rm").textContent = data.Relationship_Manager || 'N/A';
                        
                        document.getElementById("complianceDetails").style.display = "block";
                    } else {
                        document.getElementById("complianceDetails").style.display = "none";
                    }
                })
                .catch(error => {
                    console.error("Error fetching data: ", error);
                    alert("Error fetching client data.");
                });
        });
    }
    const toggleBtn = document.getElementById("toggleComplianceBtn");
    const complianceSection = document.getElementById("complianceSection");

    if (toggleBtn && complianceSection) {
    toggleBtn.addEventListener("click", function () {
        const isVisible = window.getComputedStyle(complianceSection).display === "block";
        complianceSection.style.display = isVisible ? "none" : "block";
        toggleBtn.textContent = isVisible ? "Add Compliance Info" : "Hide Compliance Info";
    });
}

    
    const addClientForm = document.getElementById("addClientForm");
    if (addClientForm) {
        addClientForm.addEventListener("submit", function(event) {
            event.preventDefault();
            
            
            
                
        const fullFormData = new FormData(addClientForm);


        fetch("/submit-pending", {
            method: "POST",
            body: fullFormData
        })
        .then(response => {
            if (!response.ok) throw new Error("Server error");
            return response.json();
        })
        .then(data => {
            alert("Client added successfully!");
            addClientForm.reset();
        })
        .catch(error => {
            console.error("Error adding client:", error);
            alert("Failed to add client.");
        });

    
        })}
    const updateClientIdInput = document.getElementById("client_id");
    if (updateClientIdInput) {
        console.log("✅ JS loaded");            
        updateClientIdInput.addEventListener("change", function () {
            console.log("🟡 Client ID changed");
            const clientId = updateClientIdInput.value;
            if (!clientId) return;

            fetch(`/client/${clientId}`)
                .then(response => {
                    console.log("🔄 Response status:", response.status);
                    return response.json();
                })
                .then(data => {
                    console.log("📦 Fetched data:", data);


                    // Fill client fields
                    document.getElementById("name").value = data.Name || '';
                    document.getElementById("date_of_birth").value = formatDate(data.Date_of_birth);
                    document.getElementById("contact_number").value = data.Contact_number || '';
                    document.getElementById("email_address").value = data.Email_address || '';
                    document.getElementById("nationality").value = data.Nationality || '';
                    document.getElementById("residency_address").value = data.Residency_address || '';
                    document.getElementById("employment_status").value = data.Employment_status || '';
                    document.getElementById("age").value = data.Age || '';
                    document.getElementById("ic_number").value = data.Ic_number || '';
                    document.getElementById("client_profile").value = data.Client_profile || '';

                    // Fill compliance fields (if present)
                    document.querySelector("[name='onboarded_date']").value = formatDate(data.Onboarded_date);
                    document.querySelector("[name='last_assessment']").value = formatDate(data.Last_periodic_risk_assessment);
                    document.querySelector("[name='next_assessment']").value = formatDate(data.Next_periodic_risk_assessment);
                    document.querySelector("[name='risk_rating']").value = data.Risk_rating || '';
                    document.querySelector("[name='relationship_manager']").value = data.Relationship_Manager || '';
                    document.querySelector("[name='service_type']").value = data.Service_type || '';
                    document.querySelector("[name='client_type']").value = data.Client_type || '';
                    document.querySelector("[name='pep']").value = data.Pep || '';
                })
                .catch(error => {
                    console.error("Error fetching client data:", error);
                    alert("Something went wrong.");
                });
        });}
    
    else{
        console.log("❌ client_id input not found");
    }
    
    
    const updateClientForm = document.getElementById("updateClientForm");
    if (updateClientForm) {
        updateClientForm.addEventListener("submit", function (event) {
            event.preventDefault();

            const formData = new FormData(updateClientForm);
            const data = {
                Client_id: formData.get("client_id"),
                Name: formData.get("name"),
                Date_of_birth: formData.get("date_of_birth"),
                Contact_number: formData.get("contact_number"),
                Email_address: formData.get("email_address"),
                Nationality: formData.get("nationality"),
                Residency_address: formData.get("residency_address"),
                Employment_status: formData.get("employment_status"),
                Age: formData.get("age"),
                IC_number: formData.get("ic_number"),
                Client_profile: formData.get("client_profile"),
                Onboarded_date: formData.get("onboarded_date"),
                Last_periodic_risk_assessment: formData.get("last_assessment"),
                Next_periodic_risk_assessment: formData.get("next_assessment"),
                Risk_rating: formData.get("risk_rating"),
                Relationship_Manager: formData.get("relationship_manager"),
                Service_type: formData.get("service_type"),
                Client_type: formData.get("client_type"),
                Pep: formData.get("pep")
            };

            fetch("/update-client", {
                method: "POST",
                headers: {
                    "Content-Type": "application/json"
                },
                body: JSON.stringify(data)
            })
                .then(response => response.json())
                .then(result => {
                    if (result.message) {
                        alert("Client updated successfully!");
                        updateClientForm.reset();
                    } else {
                        alert("Update failed: " + result.error);
                    }
                })
                .catch(error => {
                    console.error("Error updating client:", error);
                    alert("Failed to update client.");
                });
        });
    }
    const deleteBtn = document.getElementById("deleteClientBtn");

    if (deleteBtn) {
        deleteBtn.addEventListener("click", function () {
            const clientId = document.getElementById("clientId").value;
            if (!clientId) {
                alert("Please enter a Client ID first.");
                return;
            }

            if (!confirm("Are you sure you want to delete this client?")) return;

            fetch(`/delete-client/${clientId}`, {
                method: "DELETE",
            })
                .then((res) => res.json())
                .then((data) => {
                    if (data.message) {
                        alert("Client deleted successfully.");
                        document.getElementById("clientDetails").style.display = "none";
                        document.getElementById("complianceDetails").style.display = "none";
                    } else {
                        alert("Delete failed: " + data.error);
                    }
                })
                .catch((err) => {
                    console.error("Error:", err);
                    alert("An error occurred while deleting.");
                });
        });
    }

    function loadTasks() {
        fetch("/get_tasks")
            .then(response => response.json())
            .then(data => {
                const todoColumn = document.getElementById("todo-column");
                const doneColumn = document.getElementById("done-column");
                todoColumn.innerHTML = "";
                doneColumn.innerHTML = "";

                data.forEach(task => {
                    const taskBox = document.createElement("div");
                    taskBox.className = "pending-box"; // reuse pending box styling
                    taskBox.onclick = () => toggleDetails(`task-${task.id}`);
                    taskBox.innerHTML = `
                        <strong>${task.client_name}</strong> (RM: ${task.rm})
                        <div id="task-${task.id}" class="pending-details">
                            <p><strong>Documents:</strong> ${task.documents.join(", ")}</p>
                            <p><strong>Doc Link:</strong> <a href="${task.doc_link}" target="_blank">${task.doc_link}</a></p>
                            <p><strong>EMA/IMA:</strong> <a href="${task.ema_ima}" target="_blank">${task.ema_ima}</a></p>
                            <p><strong>Assigned From:</strong> ${task.assigned_from}</p>
                            <p><strong>Assigned To:</strong> ${task.assigned_to}</p>
                            <p><strong>Status:</strong> ${task.completion_status}</p>
                            <button class="delete-task" onclick="event.stopPropagation(); deleteTask(${task.id})">×</button>
                        </div>
                    `;

                    if (task.completion_status === "Done") {
                        doneColumn.appendChild(taskBox);
                    } else {
                        todoColumn.appendChild(taskBox);
                    }
                });
        })
        .catch(err => {
            console.error("Failed to load tasks:", err);
        });
        

}
    const inputs = document.querySelectorAll(".pending-details input");

  inputs.forEach(input => {
    input.addEventListener("click", function (e) {
      e.stopPropagation();
    });
  });

  const buttons = document.querySelectorAll(".pending-details button");
  buttons.forEach(button => {
    button.addEventListener("click", function (e) {
      e.stopPropagation();
    });
  });

  const forms = document.querySelectorAll(".pending-details form");
  forms.forEach(form => {
    form.addEventListener("click", function (e) {
      e.stopPropagation();
    });
  });
});
function deleteTask(id) {
    if (!confirm("Delete this task?")) return;

    fetch(`/delete_task/${id}`, {
        method: "DELETE",
    })
    .then(res => res.json())
    .then(data => {
        if (data.success) {
            loadTasks();
        } else {
            alert("Failed to delete task.");
        }
    })
    .catch(err => {
        console.error("Delete error:", err);
    });
}

function drop(ev, targetId) {
  ev.preventDefault();
  const data = ev.dataTransfer.getData("text");
  const item = document.getElementById(data);
  const taskId = data.replace("task-", "");
  console.log(`📦 Dropped task ${taskId} into ${targetId}`); // 🔍 log
  if (item && document.getElementById(targetId)) {
    document.getElementById(targetId).appendChild(item);

    // Determine the new status based on where it was dropped
    const newStatus = (targetId === "done") ? "Complete" : "Incomplete";

    // Send update to backend
    fetch(`/update_task_status/${taskId}`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json"
      },
      body: JSON.stringify({ status: newStatus })
    })
    .then(res => res.json())
    .then(data => {
      if (!data.success) {
        alert("Failed to update task status.");
        console.error(data.error);
      }
    })
    .catch(err => {
      console.error("Error updating task status:", err);
    });
  }
}
function lookupPostal() {
    const postal = document.getElementById("postal_code").value;
    const nationality = document.getElementById("nationality").value;

    if (nationality !== "Singaporean") {
        alert("Postal code lookup is only for Singaporeans.");
        return;
    }

    if (!postal || postal.length !== 6) {
        alert("Please enter a valid 6-digit postal code.");
        return;
    }

    fetch('/get-address-from-postal', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({ postal_code: postal })
    })
    .then(response => response.json())
    .then(data => {
        if (data.found > 0) {
            const result = data.results[0];
            const blk = result.BLK_NO && result.BLK_NO !== "NIL" ? `Blk ${result.BLK_NO}` : "";
            const address = `${blk} ${result.ROAD_NAME}, Singapore ${result.POSTAL}`.trim().replace(/\s+/g, ' ');
            document.getElementById("residency_address").value = address;
        } else {
            alert("No address found for this postal code.");
        }
    })
    .catch(error => {
        console.error("Error fetching address:", error);
        alert("Failed to fetch address.");
    });
}
document.addEventListener("DOMContentLoaded", function () {
    fetch("/get-all-clients")
        .then(response => response.json())
        .then(data => {
            const tbody = document.getElementById("clientTableBody");
            if (!tbody) return;

            tbody.innerHTML = "";  // Clear any existing rows

            data.forEach(client => {
                const row = document.createElement("tr");

                row.innerHTML = `
                    <td>${client.Client_id}</td>
                    <td>
                        <span class="expand-button" onclick="toggleDetails('details-${client.Client_id}')">
                            ${client.Name}
                        </span>
                    </td>
                    <td>${client.Nationality}</td>
                    <td>${client.Risk_rating || ""}</td>
                    <td><button onclick="toggleDetails('details-${client.Client_id}')">Edit</button></td>
                `;

                const detailRow = document.createElement("tr");
                detailRow.id = `details-${client.Client_id}`;
                detailRow.className = "details-section";
                detailRow.innerHTML = `
                <td colspan="10">
                    <form onsubmit="event.preventDefault(); submitClientUpdate(${client.Client_id}, this)">
                        <div style="display: flex; gap: 30px; align-items: flex-start; width: 100%; box-sizing: border-box;">

                            <!-- Left Column -->
                            <div style="flex: 1;">
                                <label>Name:</label><br>
                                <input type="text" name="Name" value="${client.Name || ""}"><br>
                                <label>Nationality:</label><br>
                                <input type="text" name="Nationality" value="${client.Nationality || ""}"><br>
                                <label>Residency Address:</label><br>
                                <input type="text" name="Residency_address" value="${client.Residency_address || ""}"><br>
                                <label>Contact Number:</label><br>
                                <input type="text" name="Contact_number" value="${client.Contact_number || ""}"><br>
                                <label>Email Address:</label><br>
                                <input type="email" name="Email_address" value="${client.Email_address || ""}"><br>
                            </div>

                            <!-- Middle Column -->
                            <div style="flex: 1;">
                                <label>Employment Status:</label><br>
                                <input type="text" name="Employment_status" value="${client.Employment_status || ""}"><br>
                                <label>IC Number:</label><br>
                                <input type="text" name="IC_number" value="${client.Ic_number || ""}"><br>
                                <label>Client Profile:</label><br>
                                <input type="text" name="Client_profile" value="${client.Client_profile || ""}"><br>
                                <label>Date of Birth:</label><br>
                                <input type="date" name="Date_of_birth" value="${formatDate(client.Date_of_birth)}"><br>
                                <label>Age:</label><br>
                                <input type="number" name="Age" value="${client.Age || ""}"><br>
                            </div>

                            <!-- Right Column (Compliance) -->
                            <div style="flex: 1;">
                                <h4>Compliance Details</h4>
                                <label>Onboarded Date:</label><br>
                                <input type="date" name="Onboarded_date" value="${formatDate(client.Onboarded_date)}"><br>
                                <label>Last Periodic Risk Assessment:</label><br>
                                <input type="date" name="Last_periodic_risk_assessment" value="${formatDate(client.Last_periodic_risk_assessment)}"><br>
                                <label>Next Periodic Risk Assessment:</label><br>
                                <input type="date" name="Next_periodic_risk_assessment" value="${formatDate(client.Next_periodic_risk_assessment)}"><br>
                                <label>Risk Rating:</label><br>
                                <input type="text" name="Risk_rating" value="${client.Risk_rating || ""}"><br>
                                <label>Relationship Manager:</label><br>
                                <input type="text" name="Relationship_Manager" value="${client.Relationship_Manager || ""}"><br>
                                <label>Service Type:</label><br>
                                <input type="text" name="Service_type" value="${client.Service_type || ""}"><br>
                                <label>Client Type:</label><br>
                                <input type="text" name="Client_type" value="${client.Client_type || ""}"><br>
                                <label>PEP:</label><br>
                                <input type="text" name="Pep" value="${client.Pep || ""}"><br>
                            </div>
                        </div>

                        <div style="margin-top: 10px;">
                            <button type="submit">Save</button>
                        </div>
                    </form>
                </td>
                `;



                tbody.appendChild(row);
                tbody.appendChild(detailRow);
            });
        })
        .catch(err => {
            console.error("Error loading client data:", err);
            alert("Failed to load client data.");
        });
});
function submitClientUpdate(clientId, form) {
    const formData = new FormData(form);
    const payload = { Client_id: clientId };
    formData.forEach((value, key) => {
        payload[key] = value;
    });

    fetch('/update-client', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify(payload)
    })
    .then(res => res.json())
    .then(data => {
        alert(data.message || "Updated successfully");
    })
    .catch(err => {
        console.error("Update failed:", err);
        alert("Failed to update client.");
    });
}
function toggleDetails(id) {
  const el = document.getElementById(id);
  if (el) {
    el.style.display = (el.style.display === "block") ? "none" : "block";
  }
}
function formatDate(rawDate) {
    if (!rawDate) return "";
    const date = new Date(rawDate);
    if (isNaN(date)) return "";  // invalid date
    return date.toISOString().split('T')[0];  // returns 'YYYY-MM-DD'
}

