import { useState } from "react";
import { useAuthContext } from "./useAuthContext";
import axios from "axios";

export const useLogin = () => {
  const [error, setError] = useState(null);
  const [isLoading, setIsLoading] = useState(false);
  const { dispatch } = useAuthContext();

  const login = async (username, password) => {
    setIsLoading(true);
    setError(null);
    console.log(username, password);
    try {
      const response = await axios.post(
        "https://login-service-v2-935294039360.us-central1.run.app/login/",
        {
          username,
          password,
        }
      );

      if (response.status === 200) {
        const { access_token, token_type } = response.data;

        // Store the token in localStorage
        localStorage.setItem(
          "user",
          JSON.stringify({
            access_token,
            token_type,
          })
        );

        // Dispatch the login action
        dispatch({
          type: "LOGIN",
          payload: { access_token, token_type },
        });

        setIsLoading(false);
      } else {
        throw new Error("Unexpected response status");
      }
    } catch (error) {
      setIsLoading(false);
      if (error.response && error.response.status === 401) {
        setError("Invalid credentials. Please try again.");
      } else if (error.response) {
        setError(error.response.data.message || "An error occurred.");
      } else if (error.request) {
        console.error("No response received:", error.request);
        setError("Unable to connect to the server. Please try again later.");
      } else {
        setError(error.message);
      }
    }
  };

  return { login, isLoading, error };
};
