import { defineStore } from "pinia";
import axios from "@/lib/axios";

export const useClientsStore = defineStore("clients", {
  state: () => ({
    clients: [],
    total: 0,
  }),
  actions: {
    async fetchClients(params = {}) {
      const res = await axios.get("/clients/", { params });
      this.clients = res.data.items;
      this.total = res.data.total;
    },
    async getClientById(id) {
      const res = await axios.get(`/clients/${id}`);
      return res.data;
    },
    async getClientWithEstimates(id, params = {}) {
      const resClient = await axios.get(`/clients/${id}`);
      const client = resClient.data;

      const resEstimates = await axios.get("/estimates/", {
        params: { client: client.id, ...params },
      });
      const estimates = resEstimates.data.items ? resEstimates.data.items : resEstimates.data;
      const total = resEstimates.data.total ?? estimates.length;

      return { client, estimates, total };
    },
    async createClient(data) {
      const res = await axios.post("/clients/", data);
      await this.fetchClients();
      return res.data;
    },
    async updateClient(id, data) {
      const res = await axios.put(`/clients/${id}`, data);
      await this.fetchClients();
      return res.data;
    },
    async deleteClient(id) {
      await axios.delete(`/clients/${id}`);
      await this.fetchClients();
    },

    async getClientLogs(id, params = {}) {
      const res = await axios.get(`/clients/${id}/logs`, { params });
      return res.data;
    },
  },
});
