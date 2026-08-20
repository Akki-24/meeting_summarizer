import axios from "axios";

const API_BASE_URL = "http://127.0.0.1:8000/api/v1";

export const uploadMeetingAudio = async (file) => {
  const formData = new FormData();
  formData.append("file", file);

  const response = await axios.post(
    `${API_BASE_URL}/meetings/upload`,
    formData,
    {
      headers: { "Content-Type": "multipart/form-data" },
    },
  );
  return response.data;
};

export const getMeeting = async (meetingId) => {
  const response = await axios.get(`${API_BASE_URL}/meetings/${meetingId}`);
  return response.data;
};

export const listMeetings = async () => {
  const response = await axios.get(`${API_BASE_URL}/meetings`);
  return response.data;
};
